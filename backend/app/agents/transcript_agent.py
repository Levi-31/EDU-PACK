import logging
from typing import List, Dict, Any, Tuple
from app.domain.enums import TranscriptStatus
from app.domain.schemas.transcript import TranscriptData, TranscriptSegment

logger = logging.getLogger(__name__)


class TranscriptChunk(BaseModel if False else object):
    def __init__(self, chunk_id: str, segments: List[TranscriptSegment]):
        self.chunk_id = chunk_id
        self.segments = segments

    @property
    def start_time(self) -> float:
        return self.segments[0].start_seconds if self.segments else 0.0

    @property
    def end_time(self) -> float:
        return self.segments[-1].end_seconds if self.segments else 0.0

    def format_with_evidence(self) -> str:
        lines = []
        for s in self.segments:
            lines.append(f"[{s.id} | {s.formatted_start}] {s.text}")
        return "\n".join(lines)


class TranscriptProcessingAgent:
    """
    Normalizes transcripts, performs quality and completeness checks,
    and applies semantic token-aware chunking preserving evidence segment mappings.
    """

    def __init__(self, max_tokens_per_chunk: int = 1500, overlap_segments: int = 2):
        self.max_tokens_per_chunk = max_tokens_per_chunk
        self.overlap_segments = overlap_segments

    def evaluate_quality(self, transcript: TranscriptData) -> Tuple[bool, str]:
        if transcript.status != TranscriptStatus.AVAILABLE and transcript.status != TranscriptStatus.USER_PROVIDED:
            return False, transcript.error_message or "Transcript not available."
        
        if not transcript.segments:
            return False, "Transcript contains no readable segments."

        total_words = sum(len(s.text.split()) for s in transcript.segments)
        if total_words < 15:
            return True, "Short transcript (minimal spoken dialogue, e.g. music/intro)."

        return True, "Transcript quality verified."

    def chunk_transcript(self, transcript: TranscriptData) -> List[TranscriptChunk]:
        """
        Splits transcript segments chronologically into bounded chunks while preserving
        segment IDs and accurate start/end timestamps.
        """
        segments = transcript.segments
        if not segments:
            return []

        chunks: List[TranscriptChunk] = []
        current_chunk_segments: List[TranscriptSegment] = []
        current_word_count = 0
        chunk_idx = 1

        # Approximation: 1 token ~ 0.75 words -> 1500 tokens ~ 1100 words
        max_words = int(self.max_tokens_per_chunk * 0.75)

        for seg in segments:
            seg_words = len(seg.text.split())
            if current_word_count + seg_words > max_words and current_chunk_segments:
                chunks.append(TranscriptChunk(f"chunk_{chunk_idx:03d}", current_chunk_segments))
                chunk_idx += 1
                # Preserve overlap segments for boundary continuity
                overlap = current_chunk_segments[-self.overlap_segments:] if len(current_chunk_segments) >= self.overlap_segments else []
                current_chunk_segments = list(overlap)
                current_word_count = sum(len(s.text.split()) for s in current_chunk_segments)

            current_chunk_segments.append(seg)
            current_word_count += seg_words

        if current_chunk_segments:
            chunks.append(TranscriptChunk(f"chunk_{chunk_idx:03d}", current_chunk_segments))

        return chunks

    def format_evidence_text(self, segments: List[TranscriptSegment]) -> str:
        """Formats segments with unambiguous segment ID tokens for LLM evidence attribution"""
        lines = []
        for s in segments:
            lines.append(f"[{s.id} @ {s.formatted_start}] {s.text}")
        return "\n".join(lines)

