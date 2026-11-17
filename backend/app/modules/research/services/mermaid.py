import logging
import re
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright

from app.agents.visual_agent import VisualDiagramAgent

logger = logging.getLogger(__name__)

MERMAID_JS_PATH = Path(__file__).resolve().parents[3] / "static" / "js" / "mermaid.min.js"


MAX_FLOWCHART_NODES = 12
MAX_NODES_ACROSS_PAGE = 4


def count_flowchart_nodes(code: str) -> int:
    """Counts labelled nodes in a flowchart; other diagram types return 0 because they lay out differently."""
    if not re.match(r"\s*(flowchart|graph)\b", code, re.IGNORECASE):
        return 0
    without_labels = re.sub(r'"[^"]*"', '""', code)
    return len(set(re.findall(r"\b([A-Za-z_]\w*)\s*[\[({]", without_labels)))


def flowchart_shape(code: str) -> tuple[int, int]:
    """Returns (ranks, widest rank) of a flowchart's layers, the way Mermaid stacks them; (0, 0) if it has no edges."""
    without_labels = re.sub(r'"[^"]*"', '""', code)
    edges = re.findall(
        r"\b(\w+)(?:\s*[\[({]+\"\"[\])}]+)?\s*(?:-->|---|-\.->|==>)\s*(?:\|[^|]*\|\s*)?(?=(\w+))",
        without_labels,
    )
    if not edges:
        return 0, 0
    rank = {node: 0 for edge in edges for node in edge}
    for _ in rank:
        for source, target in edges:
            if rank[target] < rank[source] + 1 and rank[source] + 1 < len(rank):
                rank[target] = rank[source] + 1
    layers = {}
    for node_rank in rank.values():
        layers[node_rank] = layers.get(node_rank, 0) + 1
    return len(layers), max(layers.values())


def clean_mermaid(code: Optional[str]) -> str:
    """Normalizes the source and picks the direction that fits the page, so labels aren't shrunk until unreadable."""
    cleaned = VisualDiagramAgent._clean_mermaid_dsl(code) or ""
    direction = re.match(r"\s*(?:flowchart|graph)\s+(TD|TB|BT|LR|RL)\b", cleaned, re.IGNORECASE)
    if not direction:
        return cleaned
    ranks, widest = flowchart_shape(cleaned)
    if ranks > MAX_NODES_ACROSS_PAGE:
        best = "TD"
    elif widest > MAX_NODES_ACROSS_PAGE:
        best = "LR"
    else:
        return cleaned
    return cleaned[:direction.start(1)] + best + cleaned[direction.end(1):]


async def find_mermaid_error(code: str) -> Optional[str]:
    """
    Parses a diagram with the real Mermaid library in Chromium, returning its syntax error or None if it parses.
    If Chromium itself is unavailable the diagram is let through; the PDF renderer drops anything that won't render.
    """
    if not code.strip():
        return "Mermaid source is empty."
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            try:
                page = await browser.new_page()
                await page.add_script_tag(content=MERMAID_JS_PATH.read_text(encoding="utf-8"))
                return await page.evaluate(
                    """async (code) => {
                        try {
                            await window.mermaid.parse(code);
                            return null;
                        } catch (err) {
                            return String(err.message || err);
                        }
                    }""",
                    code,
                )
            finally:
                await browser.close()
    except Exception as e:
        logger.warning("Could not validate Mermaid diagram: %s", e)
        return None
