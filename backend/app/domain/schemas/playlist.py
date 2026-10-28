from typing import List, Optional
from pydantic import BaseModel, Field
from app.domain.enums import NoteDetailLevel, PDFTheme, VideoProcessingStatus, TranscriptStatus


class PlaylistItemPreview(BaseModel):
    video_id: str
    original_position: int
    title: str
    channel_title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    duration_formatted: Optional[str] = None
    video_url: str
    is_available: bool = True
    status_note: Optional[str] = None


class PlaylistPreviewRequest(BaseModel):
    playlist_input: str = Field(description="YouTube playlist ID or full playlist URL")


class PlaylistPreviewResponse(BaseModel):
    playlist_id: str
    title: str
    description: Optional[str] = None
    channel_name: Optional[str] = None
    thumbnail_url: Optional[str] = None
    total_videos: int
    available_videos_count: int
    playlist_url: str
    videos: List[PlaylistItemPreview]
    is_mock: bool = False


class GenerationOptions(BaseModel):
    detail_level: NoteDetailLevel = NoteDetailLevel.STANDARD
    transcript_language: str = "en"
    enable_visuals: bool = True
    pdf_theme: PDFTheme = PDFTheme.EDITORIAL_NAVY
    max_revisions: int = 1
