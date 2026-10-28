import asyncio
import json
import logging
from typing import Dict, Set, Optional, AsyncGenerator
from app.db.session import SessionLocal
from app.db.repositories.event_repository import EventRepository
from app.db.repositories.job_repository import PlaylistJobRepository
from app.domain.enums import JobStatus

logger = logging.getLogger(__name__)


class JobEventBus:
    """
    Event broadcaster supporting in-process asyncio queues for real-time SSE streaming,
    along with persistent database recording for durable history.
    """

    def __init__(self):
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, job_id: str) -> AsyncGenerator[dict, None]:
        queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            if job_id not in self._subscribers:
                self._subscribers[job_id] = set()
            self._subscribers[job_id].add(queue)

        try:
            while True:
                # Wait for next event
                event = await queue.get()
                yield event
                queue.task_done()
                # Check if terminal event
                if event.get("stage") in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value, JobStatus.PARTIAL_SUCCESS.value]:
                    break
        finally:
            async with self._lock:
                if job_id in self._subscribers:
                    self._subscribers[job_id].discard(queue)
                    if not self._subscribers[job_id]:
                        del self._subscribers[job_id]

    async def publish(
        self,
        job_id: str,
        stage: str,
        message: str,
        progress: float,
        video_id: Optional[str] = None,
        data: Optional[dict] = None
    ):
        event_dict = {
            "job_id": job_id,
            "video_id": video_id,
            "stage": stage,
            "message": message,
            "progress": round(progress, 1),
            "data": data or {}
        }

        # 1. Persist to DB
        try:
            db = SessionLocal()
            try:
                repo = EventRepository(db)
                repo.log_event(
                    job_id=job_id,
                    stage=stage,
                    message=message,
                    progress=progress,
                    video_id=video_id,
                    data=data
                )
                # Also update job record progress and current_stage
                job_repo = PlaylistJobRepository(db)
                job_repo.update_status(
                    job_id=job_id,
                    status=JobStatus[stage] if stage in JobStatus.__members__ else JobStatus.GENERATING_NOTES,
                    stage=stage,
                    progress=progress
                )
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Could not persist event to DB: {e}")

        # 2. Broadcast to live SSE subscribers
        async with self._lock:
            subscribers = self._subscribers.get(job_id, set()).copy()

        for q in subscribers:
            try:
                q.put_nowait(event_dict)
            except asyncio.QueueFull:
                pass


event_bus = JobEventBus()
