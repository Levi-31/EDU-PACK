import asyncio
import json
import logging
from typing import Optional, AsyncGenerator
import redis.asyncio as aioredis
from app.core.config import settings
from app.db.session import SessionLocal
from app.db.repositories.event_repository import EventRepository
from app.db.repositories.job_repository import PlaylistJobRepository
from app.domain.enums import JobStatus

logger = logging.getLogger(__name__)


class JobEventBus:
    """
    Distributed event broadcaster leveraging Redis Pub/Sub for cross-container
    event propagation between Celery workers and FastAPI SSE handlers, backed by
    PostgreSQL persistence for durable history and reconnection replay.
    """

    def __init__(self):
        self._redis_url = settings.REDIS_URL

    async def subscribe(self, job_id: str) -> AsyncGenerator[dict, None]:
        # 1. Replay historical events from DB first
        last_timestamp = None
        db = SessionLocal()
        try:
            repo = EventRepository(db)
            past_events = repo.list_by_job(job_id)
            for ev in past_events:
                last_timestamp = ev.timestamp
                yield {
                    "job_id": ev.job_id,
                    "video_id": ev.video_id,
                    "stage": ev.stage,
                    "message": ev.message,
                    "progress": ev.progress,
                    "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                    "data": ev.data or {}
                }
                if ev.stage in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.PARTIAL_SUCCESS.value, JobStatus.CANCELLED.value]:
                    return
        except Exception as e:
            logger.warning(f"Error replaying DB events: {e}")
        finally:
            db.close()

        # 2. Subscribe to Redis PubSub for live events
        redis_client = None
        pubsub = None
        try:
            redis_client = aioredis.from_url(self._redis_url, decode_responses=True)
            pubsub = redis_client.pubsub()
            channel_name = f"events:{job_id}"
            await pubsub.subscribe(channel_name)

            while True:
                msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if msg and msg.get("type") == "message":
                    data_str = msg.get("data")
                    if data_str:
                        event_dict = json.loads(data_str)
                        yield event_dict
                        if event_dict.get("stage") in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.PARTIAL_SUCCESS.value, JobStatus.CANCELLED.value]:
                            break
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.info(f"Redis PubSub not available or interrupted ({e}), falling back to database polling...")
            # Fallback: Poll DB every second
            while True:
                await asyncio.sleep(1.0)
                db_poll = SessionLocal()
                try:
                    repo_poll = EventRepository(db_poll)
                    new_events = repo_poll.get_events_after(job_id, last_timestamp) if last_timestamp else []
                    for ev in new_events:
                        last_timestamp = ev.timestamp
                        yield {
                            "job_id": ev.job_id,
                            "video_id": ev.video_id,
                            "stage": ev.stage,
                            "message": ev.message,
                            "progress": ev.progress,
                            "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                            "data": ev.data or {}
                        }
                        if ev.stage in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.PARTIAL_SUCCESS.value, JobStatus.CANCELLED.value]:
                            return
                finally:
                    db_poll.close()
        finally:
            if pubsub:
                try:
                    await pubsub.unsubscribe()
                    await pubsub.close()
                except Exception:
                    pass
            if redis_client:
                try:
                    await redis_client.close()
                except Exception:
                    pass

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

        # 1. Persist event to DB
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
                # Update current status & progress on job record
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

        # 2. Publish to Redis Pub/Sub
        try:
            redis_client = aioredis.from_url(self._redis_url, decode_responses=True)
            await redis_client.publish(f"events:{job_id}", json.dumps(event_dict))
            await redis_client.close()
        except Exception as e:
            logger.warning(f"Could not publish event to Redis: {e}")


event_bus = JobEventBus()
