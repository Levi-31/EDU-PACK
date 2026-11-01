from datetime import datetime
from typing import Optional, List, Tuple, Any
from sqlalchemy.orm import Session
from app.db.models.research_job import ResearchJob
from app.db.repositories.base import BaseRepository


def sanitize_null_bytes(val: Any) -> Any:
    """Recursively strip NUL (0x00) characters which are rejected by PostgreSQL."""
    if isinstance(val, str):
        return val.replace("\x00", "")
    elif isinstance(val, list):
        return [sanitize_null_bytes(item) for item in val]
    elif isinstance(val, dict):
        return {sanitize_null_bytes(k): sanitize_null_bytes(v) for k, v in val.items()}
    return val


class ResearchJobRepository(BaseRepository[ResearchJob]):
    def __init__(self, db: Session):
        super().__init__(ResearchJob, db)

    def get_by_id(self, job_id: str) -> Optional[ResearchJob]:
        return self.db.query(ResearchJob).filter(ResearchJob.id == job_id).first()

    def list_jobs(self, skip: int = 0, limit: int = 20) -> Tuple[List[ResearchJob], int]:
        total = self.db.query(ResearchJob).count()
        jobs = (
            self.db.query(ResearchJob)
            .order_by(ResearchJob.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return jobs, total

    def update_stage(
        self,
        job_id: str,
        stage: str,
        progress: float,
        mode: Optional[str] = None,
        log_entry: Optional[str] = None
    ) -> Optional[ResearchJob]:
        try:
            job = self.get_by_id(job_id)
            if not job:
                return None
            job.current_stage = sanitize_null_bytes(stage)
            job.progress_percentage = round(progress, 1)
            if mode:
                job.mode = sanitize_null_bytes(mode)
            if log_entry:
                current_logs = list(job.logs_json or [])
                current_logs.append(sanitize_null_bytes(log_entry))
                job.logs_json = current_logs
            self.db.commit()
            self.db.refresh(job)
            return job
        except Exception:
            self.db.rollback()
            raise

    def complete_job(
        self,
        job_id: str,
        mode: str,
        plan_dict: Optional[dict],
        evidence_list: Optional[list],
        sections_list: Optional[list],
        image_specs: Optional[list],
        final_markdown: str,
        markdown_filename: str,
        bundle_filename: str,
        images_dir_path: str,
        logs: list,
        pdf_url: Optional[str] = None,
        bundle_url: Optional[str] = None,
        markdown_url: Optional[str] = None,
        image_urls_json: Optional[list] = None
    ) -> Optional[ResearchJob]:
        try:
            job = self.get_by_id(job_id)
            if not job:
                return None
            job.status = "COMPLETED"
            job.current_stage = "Finished"
            job.progress_percentage = 100.0
            job.mode = sanitize_null_bytes(mode)
            job.plan_json = sanitize_null_bytes(plan_dict)
            job.evidence_json = sanitize_null_bytes(evidence_list)
            job.sections_json = sanitize_null_bytes(sections_list)
            job.image_specs_json = sanitize_null_bytes(image_specs)
            job.final_markdown = sanitize_null_bytes(final_markdown)
            job.markdown_filename = sanitize_null_bytes(markdown_filename)
            job.bundle_filename = sanitize_null_bytes(bundle_filename)
            job.images_dir_path = sanitize_null_bytes(images_dir_path)
            job.logs_json = sanitize_null_bytes(logs)
            if pdf_url:
                job.pdf_url = sanitize_null_bytes(pdf_url)
            if bundle_url:
                job.bundle_url = sanitize_null_bytes(bundle_url)
            if markdown_url:
                job.markdown_url = sanitize_null_bytes(markdown_url)
            if image_urls_json:
                job.image_urls_json = sanitize_null_bytes(image_urls_json)
            job.completed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(job)
            return job
        except Exception:
            self.db.rollback()
            raise

    def update_urls(
        self,
        job_id: str,
        pdf_url: Optional[str] = None,
        bundle_url: Optional[str] = None,
        markdown_url: Optional[str] = None,
        image_urls_json: Optional[list] = None
    ) -> Optional[ResearchJob]:
        try:
            job = self.get_by_id(job_id)
            if not job:
                return None
            if pdf_url:
                job.pdf_url = sanitize_null_bytes(pdf_url)
            if bundle_url:
                job.bundle_url = sanitize_null_bytes(bundle_url)
            if markdown_url:
                job.markdown_url = sanitize_null_bytes(markdown_url)
            if image_urls_json:
                job.image_urls_json = sanitize_null_bytes(image_urls_json)
            self.db.commit()
            self.db.refresh(job)
            return job
        except Exception:
            self.db.rollback()
            raise

    def fail_job(self, job_id: str, error_message: str, logs: Optional[list] = None) -> Optional[ResearchJob]:
        try:
            job = self.get_by_id(job_id)
            if not job:
                return None
            job.status = "FAILED"
            job.current_stage = "Failed"
            job.error_message = sanitize_null_bytes(error_message)
            if logs:
                job.logs_json = sanitize_null_bytes(logs)
            self.db.commit()
            self.db.refresh(job)
            return job
        except Exception:
            self.db.rollback()
            raise

