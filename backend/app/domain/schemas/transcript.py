from typing import List, Optional
from pydantic import BaseModel, Field
from app.domain.enums import TranscriptStatus


class TranscriptSegment(BaseModel):
    id: str = Field(description="Unique segment identifier e.g. seg_001")
    start_seconds: float = Field(description="Segment start time in seconds")
    end_seconds: float = Field(description="Segment end time in seconds")
    text: str = Field(description="Spoken text within segment")

    @property
    def formatted_start(self) -> str:
        minutes = int(self.start_seconds // 60)
        seconds = int(self.start_seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"


class TranscriptData(BaseModel):
    video_id: str
    language: str = "en"
    source: str = "caption_provider"
    status: TranscriptStatus = TranscriptStatus.AVAILABLE
    segments: List[TranscriptSegment] = Field(default_factory=list)
    raw_text: Optional[str] = None
    error_message: Optional[str] = None

    @property
    def total_duration(self) -> float:
        if not self.segments:
            return 0.0
        return max(s.end_seconds for s in self.segments)

    def get_text(self) -> str:
        if self.raw_text:
            return self.raw_text
        return " ".join(s.text for s in self.segments)

