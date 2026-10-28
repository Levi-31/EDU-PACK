import logging
import re
from typing import Optional
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

    def _is_valid_mermaid(self, dsl: Optional[str]) -> bool:
        """Validate that the generated Mermaid code starts with a legitimate diagram directive."""
        if not dsl or not dsl.strip():
            return False
        first_line = dsl.strip().split("\n")[0].strip().lower()
        return any(first_line.startswith(prefix) for prefix in VALID_MERMAID_PREFIXES)

    async def evaluate_and_generate(
        self,
        notes: StructuredVideoNotes,
        enable_visuals: bool = True
    ) -> Optional[VisualAssetSchema]:
        if not enable_visuals:
            return None

        try:
            visual_spec = await self.llm.generate_visual_spec(notes)
            if not visual_spec:
                return None

            # Validate Mermaid code if present
            if visual_spec.mermaid_code:
                if not self._is_valid_mermaid(visual_spec.mermaid_code):
                    logger.warning(
                        "Generated Mermaid code for video '%s' failed prefix validation: %s",
                        notes.video_title,
                        visual_spec.mermaid_code[:100]
                    )
                    # Don't attach invalid code
                    visual_spec.mermaid_code = None
                    visual_spec.is_generated = False
                    return None

            # Attach visual to note section if specified
            if visual_spec.section_index is not None and visual_spec.section_index < len(notes.sections):
                notes.sections[visual_spec.section_index].visual = visual_spec
            elif notes.sections:
                # Default to first section if unassigned
                notes.sections[0].visual = visual_spec

            return visual_spec
        except Exception as e:
            logger.warning("Visual agent skipped due to error: %s", e)
            return None
