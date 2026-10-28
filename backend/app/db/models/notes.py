from sqlalchemy import Column, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.db.models.base import generate_uuid, TimestampMixin


class VideoNotes(Base, TimestampMixin):
    __tablename__ = "video_notes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("playlist_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id = Column(String(50), nullable=False, index=True)
    
    schema_version = Column(String(20), default="1.0", nullable=False)
    notes_json = Column(JSON, nullable=False)
    
    model_id = Column(String(100), nullable=True)
    prompt_version = Column(String(50), default="v1", nullable=False)
    review_status = Column(String(50), default="APPROVED", nullable=False)
    review_findings_json = Column(JSON, nullable=True)

    job = relationship("PlaylistJob", back_populates="notes")
