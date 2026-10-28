import logging
from typing import Dict, List, Optional
from app.domain.schemas.notes import StructuredVideoNotes
from app.domain.schemas.transcript import TranscriptData, TranscriptSegment
from app.integrations.openai.client import OpenAIClientInterface
from app.integrations.youtube.parser import construct_video_url

logger = logging.getLogger(__name__)


class TechnicalNotesAgent:
    """
    Synthesizes dense, structured technical notes grounded in transcript evidence.
    Resolves evidence segment IDs to verified start timestamps and constructs video watch links.
    """

    def __init__(self, llm_client: OpenAIClientInterface):
        self.llm = llm_client

    async def generate_notes_for_video(
        self,
        video_metadata: dict,
        transcript: TranscriptData,
        detail_level: str = "standard"
    ) -> StructuredVideoNotes:
        # Build segment lookup dict
        segment_map: Dict[str, TranscriptSegment] = {s.id: s for s in transcript.segments}
        raw_evidence = [s.model_dump() for s in transcript.segments]
        
        # Build annotated transcript text
        formatted_text = "\n".join(f"[{s.id} @ {s.formatted_start}] {s.text}" for s in transcript.segments)

        # Generate structured notes via LLM
        notes = await self.llm.generate_structured_notes(
            video_metadata=video_metadata,
            transcript_text=formatted_text,
            evidence_segments=raw_evidence,
            detail_level=detail_level
        )

        # Enforce application-code verification of timestamps
        # Never allow LLM to invent timestamps
        video_id = video_metadata.get("video_id", "")
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
                # If no segment ID could be resolved, fall back to video link without invented timestamp
                section.timestamp_seconds = None
                section.timestamped_watch_url = construct_video_url(video_id)

        return notes
