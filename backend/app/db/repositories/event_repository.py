from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models.event import JobEvent
from app.db.repositories.base import BaseRepository


class EventRepository(BaseRepository[JobEvent]):
    def __init__(self, db: Session):
        super().__init__(JobEvent, db)

    def log_event(
        self,
        job_id: str,
        stage: str,
        message: str,
        progress: float,
        video_id: Optional[str] = None,
        data: Optional[dict] = None
    ) -> JobEvent:
        event = JobEvent(
            job_id=job_id,
            video_id=video_id,
            stage=stage,
            message=message,
            progress=progress,
            data=data
        )
        return self.create(event)

    def list_by_job(self, job_id: str, limit: int = 200) -> List[JobEvent]:
        return (
            self.db.query(JobEvent)
            .filter(JobEvent.job_id == job_id)
            .order_by(JobEvent.timestamp.asc())
            .limit(limit)
            .all()
        )

    def get_events_after(self, job_id: str, after_timestamp, limit: int = 100) -> List[JobEvent]:
        return (
            self.db.query(JobEvent)
            .filter(JobEvent.job_id == job_id, JobEvent.timestamp > after_timestamp)
            .order_by(JobEvent.timestamp.asc())
            .limit(limit)
            .all()
        )

