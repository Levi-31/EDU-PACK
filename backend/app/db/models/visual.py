from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.db.models.base import generate_uuid, TimestampMixin


class VisualAsset(Base, TimestampMixin):
    __tablename__ = "visual_assets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("playlist_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id = Column(String(50), nullable=False, index=True)
    section_index = Column(Integer, nullable=True)
    
    asset_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=False)
    
    mermaid_code = Column(String, nullable=True)
    image_url = Column(String(1000), nullable=True)
    mime_type = Column(String(50), default="image/svg+xml", nullable=False)
    storage_key = Column(String(500), nullable=True)
    decision_reason = Column(String(500), nullable=True)

    job = relationship("PlaylistJob", back_populates="visuals")

