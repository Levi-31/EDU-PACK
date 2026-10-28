import logging
from typing import Optional
from app.domain.schemas.notes import StructuredVideoNotes
from app.domain.schemas.visual import VisualAssetSchema
from app.integrations.openai.client import OpenAIClientInterface

logger = logging.getLogger(__name__)


class VisualDiagramAgent:
    """
    Conditionally evaluates whether a diagram adds pedagogical value.
    Generates Mermaid architecture / sequence diagrams or concept visuals.
    Attaches asset to video notes and safely handles generation failures.
    """

    def __init__(self, llm_client: OpenAIClientInterface):
        self.llm = llm_client

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
            
            # Attach visual to note section if specified
            if visual_spec.section_index is not None and visual_spec.section_index < len(notes.sections):
                notes.sections[visual_spec.section_index].visual = visual_spec

            return visual_spec
        except Exception as e:
            logger.warning(f"Visual agent skipped due to error: {e}")
            return None
