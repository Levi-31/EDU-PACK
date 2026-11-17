import re
import asyncio
import concurrent.futures
import logging
from pathlib import Path
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from app.modules.research.config import llm
from app.modules.research.prompts import CONDENSE_MERMAID_SYSTEM, DECIDE_IMAGES_SYSTEM
from app.modules.research.models import State, GlobalImagePlan
from app.modules.research.services.factory import ServiceFactory
from app.modules.research.services.image import ClippedImageError
from app.modules.research.text_cleanup import repair_control_chars, strip_reference_notes
from app.modules.research.services.mermaid import (
    MAX_FLOWCHART_NODES,
    clean_mermaid,
    count_flowchart_nodes,
    find_mermaid_error,
)

logger = logging.getLogger(__name__)

def merge_content(state: State) -> dict:
    """
    Combines written sections into a single markdown body.
    """
    plan = state["plan"]
    if plan is None:
        raise ValueError("merge_content called without plan.")
    ordered_sections = [md for _, md in sorted(state["sections"], key=lambda x: x[0])]
    body = "\n\n".join(ordered_sections).strip()
    merged_md = strip_reference_notes(repair_control_chars(f"# {plan.blog_title}\n\n{body}\n"))
    return {"merged_md": merged_md}

def decide_images(state: State) -> dict:
    """
    Decides where to place images and drafts their generation prompts.
    """
    planner = llm.with_structured_output(GlobalImagePlan)
    merged_md = state["merged_md"]
    plan = state["plan"]
    assert plan is not None

    image_plan = planner.invoke(
        [
            SystemMessage(content=DECIDE_IMAGES_SYSTEM),
            HumanMessage(
                content=(
                    f"Blog kind: {plan.blog_kind}\n"
                    f"Topic: {state['topic']}\n\n"
                    "Propose visuals for this document.\n\n"
                    f"{merged_md}"
                )
            ),
        ]
    )

    return {
        "md_with_placeholders": image_plan.md_with_placeholders,
        "image_specs": [img.model_dump() for img in image_plan.images],
    }

def _normalize_words(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _find_headings(lines: list[str]) -> list[tuple[int, str]]:
    """Returns (line index, text) for section headings, ignoring # lines inside code fences."""
    headings, in_fence = [], False
    for idx, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        match = None if in_fence else re.match(r"#{2,3}\s+(.+)", line)
        if match:
            headings.append((idx, match.group(1)))
    return headings


def _find_section_line(lines: list[str], spec: dict) -> int | None:
    """Finds the section for a visual: the planner's heading if it matches, else the heading sharing the most words with its caption."""
    headings = _find_headings(lines)
    wanted = _normalize_words(spec.get("section_heading") or "")
    if wanted:
        for idx, text in headings:
            if _normalize_words(text) == wanted:
                return idx
        for idx, text in headings:
            if wanted in _normalize_words(text) or _normalize_words(text) in wanted:
                return idx
    description = {w for w in _normalize_words(f"{spec.get('caption', '')} {spec.get('alt', '')}").split() if len(w) > 3}
    scored = [(len(description & set(_normalize_words(text).split())), -idx, idx) for idx, text in headings]
    best = max(scored, default=(0, 0, None))
    return best[2] if best[0] > 0 else None


def _after_first_paragraph(lines: list[str], heading_idx: int) -> int:
    """Returns the line index just after a section's first paragraph, so a visual sits among the text it illustrates."""
    idx = heading_idx + 1
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    while idx < len(lines) and lines[idx].strip() and not lines[idx].startswith("#"):
        idx += 1
    return idx


def place_visuals_in_sections(md: str, image_specs: list[dict]) -> str:
    """Moves each placeholder into the section discussing its topic; the planner often leaves them at the end of long documents."""
    for spec in image_specs:
        placeholder = spec["placeholder"]
        without_placeholder = md.replace(placeholder, "").splitlines()
        section_line = _find_section_line(without_placeholder, spec)
        if section_line is None:
            logger.warning("No section found for %s (%s)", placeholder, spec.get("caption"))
            continue
        insert_at = _after_first_paragraph(without_placeholder, section_line)
        without_placeholder[insert_at:insert_at] = ["", placeholder, ""]
        md = "\n".join(without_placeholder) + "\n"
    return md


async def _condense_oversized_mermaid(code: str) -> str:
    """Asks the LLM once to shrink an oversized flowchart; keeps the original if the rewrite isn't an improvement."""
    if count_flowchart_nodes(code) <= MAX_FLOWCHART_NODES:
        return code
    try:
        response = await llm.ainvoke([SystemMessage(content=CONDENSE_MERMAID_SYSTEM), HumanMessage(content=code)])
        condensed = clean_mermaid(response.content)
    except Exception as e:
        logger.warning("Could not condense oversized Mermaid diagram: %s", e)
        return code
    if count_flowchart_nodes(condensed) < count_flowchart_nodes(code) and not await find_mermaid_error(condensed):
        return condensed
    return code

def _safe_slug(title: str) -> str:
    s = title.strip().lower()
    s = re.sub(r"[^a-z0-9 _-]+", "", s)
    s = re.sub(r"\s+", "_", s).strip("_")
    return s or "blog"

def generate_and_place_images(state: State) -> dict:
    """
    Generates images via the image service and places them in the final markdown document.
    Processes all image generation tasks concurrently using asyncio.run.
    """
    image_service = ServiceFactory.get_image_generator()
    
    plan = state["plan"]
    assert plan is not None

    # Always the writers' own text: a copy re-typed by the planner comes back with damaged punctuation
    md = state.get("merged_md") or state.get("md_with_placeholders") or ""
    image_specs = state.get("image_specs", []) or []
    md = place_visuals_in_sections(md, image_specs)

    out_dir_str = state.get("output_dir")
    base_dir = Path(out_dir_str) if out_dir_str else Path(".")
    base_dir.mkdir(parents=True, exist_ok=True)

    # If no images requested, just write merged markdown
    if not image_specs:
        filename = f"{_safe_slug(plan.blog_title)}.md"
        out_path = base_dir / filename
        out_path.write_text(md, encoding="utf-8")
        return {"final": md}

    images_dir = base_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    async def run_async_gen() -> list[tuple[str, str]]:
        # Helper function to generate a single image spec asynchronously
        async def process_spec(spec: dict) -> tuple[str, str]:
            placeholder = spec["placeholder"]
            filename = spec["filename"]
            out_path = images_dir / filename

            if spec.get("kind") == "mermaid":
                code = await _condense_oversized_mermaid(clean_mermaid(spec.get("mermaid_code")))
                error = await find_mermaid_error(code)
                if not error:
                    return placeholder, f"```mermaid\n{code}\n```\n*{spec['caption']}*"
                logger.warning("Mermaid for %s does not parse, falling back to an image: %s", placeholder, error)

            if not out_path.exists():
                try:
                    # API call is async
                    img_bytes = await image_service.generate_image_bytes(spec["prompt"])
                    # Non-blocking file writing
                    await asyncio.to_thread(out_path.write_bytes, img_bytes)
                except ClippedImageError as e:
                    # A missing diagram reads better than one with parts cut off
                    logger.warning("Omitting image %s: %s", filename, e)
                    return placeholder, ""
                except Exception as e:
                    # Graceful fallback: keep doc usable
                    prompt_block = (
                        f"> **[IMAGE GENERATION FAILED]** {spec.get('caption','')}\n>\n"
                        f"> **Alt:** {spec.get('alt','')}\n>\n"
                        f"> **Prompt:** {spec.get('prompt','')}\n>\n"
                        f"> **Error:** {e}\n"
                    )
                    return placeholder, prompt_block

            img_md = f"![{spec['alt']}](images/{filename})\n*{spec['caption']}*"
            return placeholder, img_md

        # Run all image generations concurrently
        return await asyncio.gather(*(process_spec(spec) for spec in image_specs))

    # Safe execution across both standalone threads and active asyncio loops
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            results = pool.submit(lambda: asyncio.run(run_async_gen())).result()
    else:
        results = asyncio.run(run_async_gen())

    # Apply replacements
    for placeholder, replacement in results:
        md = md.replace(placeholder, replacement)
    md = repair_control_chars(md)

    # Write final file
    filename = f"{_safe_slug(plan.blog_title)}.md"
    out_path = base_dir / filename
    out_path.write_text(md, encoding="utf-8")
    
    return {"final": md}

# Build reducer subgraph
reducer_graph = StateGraph(State)
reducer_graph.add_node("merge_content", merge_content)
reducer_graph.add_node("decide_images", decide_images)
reducer_graph.add_node("generate_and_place_images", generate_and_place_images)
reducer_graph.add_edge(START, "merge_content")
reducer_graph.add_edge("merge_content", "decide_images")
reducer_graph.add_edge("decide_images", "generate_and_place_images")
reducer_graph.add_edge("generate_and_place_images", END)
reducer_subgraph = reducer_graph.compile()
