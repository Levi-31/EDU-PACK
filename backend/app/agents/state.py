from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.domain.enums import VideoProcessingStatus, JobStatus
from app.domain.schemas.playlist import GenerationOptions
from app.domain.schemas.transcript import TranscriptData
from app.domain.schemas.notes import StructuredVideoNotes, ReviewReport
from app.domain.schemas.visual import VisualAssetSchema
from app.domain.schemas.topic_plan import VideoTopicPlan
from app.domain.schemas.research import VideoResearchBundle


class VideoGraphItem(BaseModel):
    video_id: str
    original_position: int
    title: str
    channel_title: Optional[str] = None
    description: Optional[str] = None
    duration_seconds: Optional[int] = None
    thumbnail_url: Optional[str] = None
    video_url: str
    is_available: bool = True
    
    # Processing state
    status: VideoProcessingStatus = VideoProcessingStatus.PENDING
    transcript: Optional[TranscriptData] = None
    topic_plan: Optional[VideoTopicPlan] = None
    research_bundle: Optional[VideoResearchBundle] = None
    notes: Optional[StructuredVideoNotes] = None
    visual: Optional[VisualAssetSchema] = None
    review: Optional[ReviewReport] = None
    revision_attempts: int = 0
    failure_reason: Optional[str] = None


class PlaylistGraphState(BaseModel):
    job_id: str
    playlist_id: str
    playlist_title: str
    playlist_url: str
    channel_name: Optional[str] = None
    options: GenerationOptions = Field(default_factory=GenerationOptions)
    
    videos: List[VideoGraphItem] = Field(default_factory=list)
    current_index: int = 0
    current_stage: str = "INITIALIZED"
    overall_progress: float = 0.0
    
    pdf_artifact_path: Optional[str] = None
    pdf_artifact_id: Optional[str] = None
    error_summary: Optional[str] = None
    is_cancelled: bool = False
