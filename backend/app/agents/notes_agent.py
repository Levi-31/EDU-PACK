import logging
from typing import Dict, List, Optional
from app.domain.schemas.notes import StructuredVideoNotes, ReviewReport
from app.domain.schemas.transcript import TranscriptData, TranscriptSegment
from app.domain.schemas.topic_plan import VideoTopicPlan
from app.domain.schemas.research import VideoResearchBundle
from app.integrations.openai.client import OpenAIClientInterface
from app.integrations.youtube.parser import construct_video_url

logger = logging.getLogger(__name__)


class TechnicalNotesAgent:
    """
    Synthesizes dense, structured technical notes grounded in transcript evidence,
    enriched with topic plans, foundational theory, and authoritative external research.
    Resolves evidence segment IDs to verified start timestamps and constructs video watch links.
    """

    def __init__(self, llm_client: OpenAIClientInterface):
        self.llm = llm_client

    def _ground_timestamps(
        self,
        notes: StructuredVideoNotes,
        segment_map: Dict[str, TranscriptSegment],
        video_id: str
    ):
        """Enforces application-code verification of timestamps. Never allows LLM to invent timestamps."""
        for section in notes.sections:
            valid_starts: List[float] = []
            for seg_id in section.evidence_segment_ids:
                if seg_id in segment_map:
                    valid_starts.append(segment_map[seg_id].start_seconds)

            if valid_starts:
                earliest_start = min(valid_starts)
                section.timestamp_seconds = earliest_start
                section.timestamped_watch_url = construct_video_url(video_id, earliest_start)
            else:
                section.timestamp_seconds = None
                section.timestamped_watch_url = construct_video_url(video_id)

    async def generate_notes_for_video(
        self,
        video_metadata: dict,
        transcript: TranscriptData,
        detail_level: str = "standard",
        topic_plan: Optional[VideoTopicPlan] = None,
        research_bundle: Optional[VideoResearchBundle] = None
    ) -> StructuredVideoNotes:
        segment_map: Dict[str, TranscriptSegment] = {s.id: s for s in transcript.segments}
        raw_evidence = [s.model_dump() for s in transcript.segments]
        formatted_text = "\n".join(f"[{s.id} @ {s.formatted_start}] {s.text}" for s in transcript.segments)

        notes = await self.llm.generate_structured_notes(
            video_metadata=video_metadata,
            transcript_text=formatted_text,
            evidence_segments=raw_evidence,
            detail_level=detail_level,
            topic_plan=topic_plan,
            research_bundle=research_bundle
        )

        video_id = video_metadata.get("video_id", "")
        self._ground_timestamps(notes, segment_map, video_id)
        return notes

    async def revise_notes_for_video(
        self,
        video_metadata: dict,
        transcript: TranscriptData,
        notes: StructuredVideoNotes,
        review: ReviewReport,
        research_bundle: Optional[VideoResearchBundle] = None
    ) -> StructuredVideoNotes:
        segment_map: Dict[str, TranscriptSegment] = {s.id: s for s in transcript.segments}
        transcript_text = transcript.get_text()

        revised = await self.llm.revise_notes(
            notes=notes,
            review=review,
            transcript_text=transcript_text,
            research_bundle=research_bundle
        )

        video_id = video_metadata.get("video_id", "")
        self._ground_timestamps(revised, segment_map, video_id)
        return revised
