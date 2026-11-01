import logging
import re
from typing import Optional
from app.core.config import settings
from app.domain.enums import VisualType
from app.domain.schemas.notes import StructuredVideoNotes
from app.domain.schemas.visual import VisualAssetSchema
from app.integrations.openai.client import OpenAIClientInterface

logger = logging.getLogger(__name__)

VALID_MERMAID_PREFIXES = (
    "graph",
    "flowchart",
    "sequencediagram",
    "statediagram",
    "statediagram-v2",
    "classdiagram",
    "erdiagram",
    "gantt",
    "pie",
    "gitgraph"
)


class VisualDiagramAgent:
    """
    Conditionally evaluates whether a diagram adds pedagogical value.
    Generates Mermaid architecture / sequence diagrams or concept visuals.
    Validates Mermaid DSL syntax, attaches asset to video notes, and safely handles generation failures.
    """

    def __init__(self, llm_client: OpenAIClientInterface):
        self.llm = llm_client

    @staticmethod
    def _clean_mermaid_dsl(dsl: Optional[str]) -> Optional[str]:
        """
        Strip markdown fences (```mermaid ... ```), normalize arrows, separate joined statements,
        and remove saturated manual color overrides.
        """
        if not dsl:
            return None
        text = dsl.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        # 1. Ensure newline after flowchart/graph declaration if joined on the first line
        text = re.sub(
            r"^(flowchart\s+[A-Za-z]{2}|graph\s+[A-Za-z]{2})\s*;?\s+([^\n]+)$",
            r"\1\n    \2",
            text,
            flags=re.MULTILINE | re.IGNORECASE
        )

        # 2. Split joined statements on a single line (e.g. A["X"] --> B["Y"] C["Z"] --> D["W"])
        text = re.sub(r"(\]|\)|\})\s+([A-Za-z0-9_]+\s*(?:-->|---|-.->|==>|->>|\[|\())", r"\1\n    \2", text)
        text = re.sub(r"(\]|\)|\})\s+(subgraph\b)", r"\1\n\2", text, flags=re.IGNORECASE)
        text = re.sub(r"\bend\s+([A-Za-z0-9_]+\b)", r"end\n    \1", text, flags=re.IGNORECASE)
        text = re.sub(r"\bend\s+(subgraph\b)", r"end\n\1", text, flags=re.IGNORECASE)

        # 3. Fix single-dash arrows (->) and flowchart invalid (-->>) to standard Mermaid double-dash arrows (-->)
        text = re.sub(r"-->>", "-->", text)
        text = re.sub(r"(?<![-=.])->(?!>)", "-->", text)

        # 4. Clean trailing semicolons that break subgraphs and statements
        text = re.sub(r";\s*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"\bend\s*;", "end", text, flags=re.IGNORECASE)

        # 5. Enforce editorial theme: strip manual magenta / neon / rainbow style overrides
        text = re.sub(r"(?i)\bstyle\s+[A-Za-z0-9_]+\s+fill:\s*(?:#[0-9a-fA-F]{3,8}|[a-zA-Z]+)[^;\n]*;?", "", text)
        return text.strip()

    @staticmethod
    def _auto_repair_mermaid(dsl: str) -> str:
        """Attempt to auto-close dangling brackets or unclosed subgraphs in Mermaid code."""
        text = dsl.strip()
        # Balance subgraphs
        subgraphs = len(re.findall(r"^\s*subgraph\b", text, re.IGNORECASE | re.MULTILINE))
        ends = len(re.findall(r"^\s*end\b", text, re.IGNORECASE | re.MULTILINE))
        if subgraphs > ends:
            text += "\n" + "\n".join(["end"] * (subgraphs - ends))

        # Balance brackets
        open_sq = text.count("[") - text.count("]")
        if open_sq > 0:
            text += "]" * open_sq

        # Balance quotes
        if text.count('"') % 2 != 0:
            text += '"'

        # Remove dangling arrow on last line
        lines = text.splitlines()
        if lines and lines[-1].strip().endswith(("-->", "->", "-.->", "==>")):
            lines[-1] = re.sub(r"\s*(?:-->|->|-.->|==>)\s*$", "", lines[-1])
            text = "\n".join(lines)

        return text

    def _is_valid_mermaid(self, dsl: Optional[str]) -> bool:
        """Validate that the generated Mermaid code is structurally sound and syntax-error-free."""
        clean = self._clean_mermaid_dsl(dsl)
        if not clean or len(clean.strip()) < 10:
            return False

        lines = [line.strip() for line in clean.splitlines() if line.strip()]
        if len(lines) < 2:
            return False

        first_line = lines[0].lower()
        if not any(first_line.startswith(prefix) for prefix in VALID_MERMAID_PREFIXES):
            return False

        # Check for unclosed or truncated final line
        last_line = lines[-1]
        if last_line.endswith(("[", "(", "{", "-->", "--", "->", "|", "subgraph")):
            return False

        # Validate matching subgraphs and ends
        subgraph_count = len(re.findall(r"^\s*subgraph\b", clean, re.IGNORECASE | re.MULTILINE))
        end_count = len(re.findall(r"^\s*end\b", clean, re.IGNORECASE | re.MULTILINE))
        if subgraph_count != end_count:
            return False

        # Validate balanced brackets
        if clean.count("[") != clean.count("]"):
            return False
        # In sequence diagrams, -) represents an asynchronous message arrow
        paren_text = re.sub(r"-\)", "--", clean)
        if paren_text.count("(") != paren_text.count(")"):
            return False
        if clean.count("{") != clean.count("}"):
            return False

        # Validate balanced quotes
        if clean.count('"') % 2 != 0:
            return False

        # Validate presence of diagram relationships or declared nodes
        has_edge = bool(re.search(r"-->|---|-.->|==>|->>|->", clean))
        has_nodes = len(re.findall(r"[A-Za-z0-9_]+\s*[\(\[\{]", clean)) >= 2
        return has_edge or has_nodes

    async def evaluate_and_generate(
        self,
        notes: StructuredVideoNotes,
        enable_visuals: bool = True
    ) -> Optional[VisualAssetSchema]:
        if not enable_visuals:
            return None

        try:
            visual_spec = await self.llm.generate_visual_spec(notes)
            if not visual_spec or visual_spec.asset_type == VisualType.NONE:
                return None

            # Clean and validate Mermaid code if present
            if visual_spec.mermaid_code:
                cleaned_code = self._clean_mermaid_dsl(visual_spec.mermaid_code)
                if not self._is_valid_mermaid(cleaned_code):
                    # Attempt auto-repair of syntax glitches
                    repaired = self._auto_repair_mermaid(cleaned_code)
                    if self._is_valid_mermaid(repaired):
                        cleaned_code = repaired
                    else:
                        logger.warning(
                            "Generated Mermaid code for video '%s' failed validation; visual omitted (no default/hardcoded flowchart)",
                            notes.video_title
                        )
                        visual_spec.mermaid_code = None
                        visual_spec.is_generated = False
                else:
                    visual_spec.mermaid_code = cleaned_code
                    visual_spec.is_generated = True

            # If visual spec is an illustration or has no mermaid code, check if concept image should be dynamically generated
            if (visual_spec.asset_type == VisualType.CONCEPT_ILLUSTRATION or not visual_spec.mermaid_code) and not visual_spec.image_url:
                if settings.ENABLE_IMAGE_GENERATION and visual_spec.title:
                    try:
                        img_prompt = f"{notes.video_title}: {visual_spec.title}. {visual_spec.description}"
                        img_url = await self.llm.generate_image(img_prompt)
                        if img_url:
                            visual_spec.image_url = img_url
                            visual_spec.is_generated = True
                    except Exception as img_err:
                        logger.warning("Dynamic image generation skipped for visual spec: %s", img_err)

            # Ensure we only attach if genuine mermaid code or generated image exists
            if not visual_spec.mermaid_code and not visual_spec.image_url:
                return None

            visual_spec.is_generated = True

            # Attach visual to note section if specified
            if visual_spec.section_index is not None and visual_spec.section_index < len(notes.sections):
                notes.sections[visual_spec.section_index].visual = visual_spec
            elif notes.sections:
                notes.sections[0].visual = visual_spec

            return visual_spec
        except Exception as e:
            logger.warning("Visual agent skipped due to error: %s", e)
            return None
