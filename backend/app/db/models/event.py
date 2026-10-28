from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.db.models.base import generate_uuid


class JobEvent(Base):
    __tablename__ = "job_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("playlist_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id = Column(String(50), nullable=True, index=True)
    
    stage = Column(String(100), nullable=False)
    message = Column(String(1000), nullable=False)
    progress = Column(Float, default=0.0, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    data = Column(JSON, nullable=True)

    job = relationship("PlaylistJob", back_populates="events")
