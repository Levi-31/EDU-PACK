from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.domain.enums import JobStatus, VideoProcessingStatus, TranscriptStatus
from app.domain.schemas.playlist import GenerationOptions, PlaylistItemPreview
from app.domain.schemas.artifact import ArtifactSchema


class CreateJobRequest(BaseModel):
    playlist_input: str = Field(description="YouTube video URL, playlist ID or full playlist URL")
    options: Optional[GenerationOptions] = Field(default_factory=GenerationOptions)
    title_override: Optional[str] = None
    selected_video_ids: Optional[List[str]] = Field(default=None, description="Optional list of specific video IDs to include. If omitted or empty, all videos in the playlist are included.")


class VideoStatusSchema(BaseModel):
    video_id: str
    original_position: int
    title: str
    channel_title: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_formatted: Optional[str] = None
    status: VideoProcessingStatus
    transcript_status: TranscriptStatus
    error_message: Optional[str] = None
    has_notes: bool = False
    has_visual: bool = False


class JobEventSchema(BaseModel):
    id: Optional[str] = None
    job_id: str
    video_id: Optional[str] = None
    stage: str
    message: str
    progress: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Optional[Dict[str, Any]] = None


class JobDetailResponse(BaseModel):
    id: str
    playlist_id: str
    playlist_url: str
    playlist_title: str
    status: JobStatus
    progress_percentage: float
    current_stage: str
    options: GenerationOptions
    total_videos: int
    completed_videos: int
    failed_videos: int
    skipped_videos: int
    error_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    artifact: Optional[ArtifactSchema] = None
    pdf_url: Optional[str] = None
    videos: List[VideoStatusSchema] = Field(default_factory=list)
    is_mock: bool = False
    source_type: str = "playlist"  # "video" or "playlist"
    video_id: Optional[str] = None


class JobListResponse(BaseModel):
    jobs: List[JobDetailResponse]
    total: int
    page: int
    page_size: int

