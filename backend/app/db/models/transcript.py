from sqlalchemy import Column, String, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.db.models.base import generate_uuid, TimestampMixin


class Transcript(Base, TimestampMixin):
    __tablename__ = "transcripts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("playlist_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id = Column(String(50), nullable=False, index=True)
    
    source = Column(String(50), nullable=False, default="youtube")
    language = Column(String(10), nullable=False, default="en")
    status = Column(String(50), nullable=False, default="AVAILABLE")
    
    transcript_hash = Column(String(64), nullable=True)
    segments_json = Column(JSON, nullable=False, default=list)
    raw_text = Column(String, nullable=True)
    error_message = Column(String(1000), nullable=True)

    job = relationship("PlaylistJob", back_populates="transcripts")
