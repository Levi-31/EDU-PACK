from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.db.models.base import generate_uuid, TimestampMixin


class PlaylistJob(Base, TimestampMixin):
    __tablename__ = "playlist_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    playlist_id = Column(String(100), nullable=False, index=True)
    playlist_url = Column(String(500), nullable=False)
    playlist_title = Column(String(255), nullable=False)
    channel_name = Column(String(255), nullable=True)
    
    status = Column(String(50), nullable=False, default="QUEUED", index=True)
    current_stage = Column(String(100), nullable=False, default="Initialized")
    progress_percentage = Column(Float, default=0.0, nullable=False)
    
    options = Column(JSON, nullable=False, default=dict)
    
    total_videos = Column(Integer, default=0, nullable=False)
    completed_videos = Column(Integer, default=0, nullable=False)
    failed_videos = Column(Integer, default=0, nullable=False)
    skipped_videos = Column(Integer, default=0, nullable=False)
    
    error_summary = Column(String(1000), nullable=True)
    completed_at = Column(DateTime, nullable=True)
    is_mock = Column(Boolean, default=False, nullable=False)

    # Relationships
    videos = relationship("PlaylistVideo", back_populates="job", cascade="all, delete-orphan", order_by="PlaylistVideo.original_position")
    transcripts = relationship("Transcript", back_populates="job", cascade="all, delete-orphan")
    notes = relationship("VideoNotes", back_populates="job", cascade="all, delete-orphan")
    visuals = relationship("VisualAsset", back_populates="job", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="job", cascade="all, delete-orphan")
    events = relationship("JobEvent", back_populates="job", cascade="all, delete-orphan", order_by="JobEvent.timestamp")
