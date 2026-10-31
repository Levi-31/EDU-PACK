from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.db.models.base import generate_uuid, TimestampMixin


class PlaylistVideo(Base, TimestampMixin):
    __tablename__ = "playlist_videos"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("playlist_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id = Column(String(50), nullable=False, index=True)
    playlist_item_id = Column(String(100), nullable=True)
    original_position = Column(Integer, nullable=False, default=0, index=True)
    
    title = Column(String(1000), nullable=False)
    channel_title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    thumbnail_url = Column(String(1000), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    video_url = Column(String(500), nullable=False)
    
    processing_status = Column(String(50), default="PENDING", nullable=False, index=True)
    transcript_status = Column(String(50), default="NOT_FETCHED", nullable=False)
    failure_reason = Column(Text, nullable=True)
    
    retry_count = Column(Integer, default=0, nullable=False)
    processed_at = Column(DateTime, nullable=True)

    job = relationship("PlaylistJob", back_populates="videos")

