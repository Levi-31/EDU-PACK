from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.db.models.base import generate_uuid, TimestampMixin


class Artifact(Base, TimestampMixin):
    __tablename__ = "artifacts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("playlist_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    artifact_type = Column(String(50), nullable=False, default="pdf_notes")
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(1000), nullable=False)
    mime_type = Column(String(100), default="application/pdf", nullable=False)
    file_size_bytes = Column(Integer, default=0, nullable=False)
    checksum_sha256 = Column(String(64), nullable=False)
    
    is_valid = Column(Boolean, default=True, nullable=False)

    job = relationship("PlaylistJob", back_populates="artifacts")

