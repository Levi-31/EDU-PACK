from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.db.models.job import PlaylistJob
from app.db.repositories.base import BaseRepository
from app.domain.enums import JobStatus


class PlaylistJobRepository(BaseRepository[PlaylistJob]):
    def __init__(self, db: Session):
        super().__init__(PlaylistJob, db)

    def get_by_id(self, job_id: str) -> Optional[PlaylistJob]:
        return self.db.query(PlaylistJob).filter(PlaylistJob.id == job_id).first()

    def list_jobs(self, skip: int = 0, limit: int = 20) -> Tuple[List[PlaylistJob], int]:
        total = self.db.query(PlaylistJob).count()
        jobs = (
            self.db.query(PlaylistJob)
            .order_by(PlaylistJob.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return jobs, total

    def update_status(
        self,
        job_id: str,
        status: JobStatus,
        stage: Optional[str] = None,
        progress: Optional[float] = None,
        error_summary: Optional[str] = None,
        completed_videos: Optional[int] = None,
        failed_videos: Optional[int] = None,
        skipped_videos: Optional[int] = None
    ) -> Optional[PlaylistJob]:
        job = self.get_by_id(job_id)
        if not job:
            return None
        job.status = status.value if hasattr(status, "value") else str(status)
        if stage is not None:
            job.current_stage = stage
        if progress is not None:
            job.progress_percentage = round(progress, 1)
        if error_summary is not None:
            job.error_summary = error_summary
        if completed_videos is not None:
            job.completed_videos = completed_videos
        if failed_videos is not None:
            job.failed_videos = failed_videos
        if skipped_videos is not None:
            job.skipped_videos = skipped_videos
        if status in [JobStatus.COMPLETED, JobStatus.PARTIAL_SUCCESS, JobStatus.FAILED, JobStatus.CANCELLED]:
            job.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(job)
        return job

    def increment_counters(
        self,
        job_id: str,
        completed_delta: int = 0,
        failed_delta: int = 0,
        skipped_delta: int = 0
    ) -> Optional[PlaylistJob]:
        job = self.get_by_id(job_id)
        if not job:
            return None
        job.completed_videos += completed_delta
        job.failed_videos += failed_delta
        job.skipped_videos += skipped_delta
        self.db.commit()
        self.db.refresh(job)
        return job
