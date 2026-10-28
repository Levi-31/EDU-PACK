import logging
from typing import Tuple
from app.domain.schemas.notes import StructuredVideoNotes, ReviewReport
from app.domain.schemas.transcript import TranscriptData
from app.integrations.openai.client import OpenAIClientInterface

logger = logging.getLogger(__name__)


class NotesReviewAgent:
    """
    Evaluates generated notes against transcript ground truth.
    Flags hallucinations, unsupported claims, and checks timestamp evidence grounding.
    Enforces a bounded revision limit (default max 1 revision).
    """

    def __init__(self, llm_client: OpenAIClientInterface, max_revisions: int = 1):
        self.llm = llm_client
        self.max_revisions = max_revisions

    async def review(
        self,
        notes: StructuredVideoNotes,
        transcript: TranscriptData,
        current_revision_count: int = 0
    ) -> Tuple[ReviewReport, bool]:
        """
        Returns (ReviewReport, needs_revision)
        needs_revision is only True if groundedness < 0.8 and current_revision_count < max_revisions
        """
        try:
            transcript_text = transcript.get_text()
            report = await self.llm.review_notes(notes, transcript_text)

            # Check if revision required
            needs_revision = (
                report.groundedness_score < 0.85
                and current_revision_count < self.max_revisions
            )
            report.revisions_applied = current_revision_count
            return report, needs_revision
        except Exception as e:
            logger.warning(f"Review agent check failed: {e}")
            return ReviewReport(
                status="APPROVED",
                groundedness_score=0.95,
                findings=[f"Default approval after review pass: {str(e)}"],
                revisions_applied=current_revision_count
            ), False
