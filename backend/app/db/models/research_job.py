from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, JSON, Text, Boolean
from app.db.session import Base
from app.db.models.base import generate_uuid, TimestampMixin


class ResearchJob(Base, TimestampMixin):
    """
    Persisted entity for Levi-31/Research-Tool jobs.
    Preserves topic, as-of date, router mode, evidence, article plan,
    generated markdown, image specifications, execution logs, and output bundle.
    """
    __tablename__ = "research_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    topic = Column(Text, nullable=False)
    as_of = Column(String(50), nullable=False)
    mode = Column(String(50), nullable=False, default="closed_book")  # closed_book, hybrid, open_book
    status = Column(String(50), nullable=False, default="QUEUED", index=True)  # QUEUED, RUNNING, COMPLETED, FAILED
    current_stage = Column(String(100), nullable=False, default="Initialized")
    progress_percentage = Column(Float, default=0.0, nullable=False)

    queries_json = Column(JSON, nullable=True, default=list)
    evidence_json = Column(JSON, nullable=True, default=list)
    plan_json = Column(JSON, nullable=True)
    sections_json = Column(JSON, nullable=True, default=list)
    image_specs_json = Column(JSON, nullable=True, default=list)

    final_markdown = Column(Text, nullable=True)
    markdown_filename = Column(String(255), nullable=True)
    bundle_filename = Column(String(255), nullable=True)
    images_dir_path = Column(String(500), nullable=True)

    pdf_url = Column(String(1000), nullable=True)
    bundle_url = Column(String(1000), nullable=True)
    markdown_url = Column(String(1000), nullable=True)
    image_urls_json = Column(JSON, nullable=True, default=list)

    error_message = Column(Text, nullable=True)
    logs_json = Column(JSON, nullable=True, default=list)
    is_mock = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)

