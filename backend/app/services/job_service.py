import asyncio
import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import JobNotFoundException
from app.domain.enums import JobStatus, VideoProcessingStatus, TranscriptStatus
from app.domain.schemas.job import (
    CreateJobRequest,
    JobDetailResponse,
    JobListResponse,
    VideoStatusSchema
)
from app.domain.schemas.playlist import GenerationOptions
from app.domain.schemas.artifact import ArtifactSchema
from app.db.models.job import PlaylistJob
from app.db.models.video import PlaylistVideo
from app.db.repositories.job_repository import PlaylistJobRepository
from app.db.repositories.video_repository import PlaylistVideoRepository
from app.db.repositories.artifact_repository import ArtifactRepository
from app.db.repositories.notes_repository import NotesRepository
from app.services.playlist_service import PlaylistService
from app.workers.tasks import run_playlist_job

logger = logging.getLogger(__name__)


class JobService:
    def __init__(self, db: Session):
        self.db = db
        self.job_repo = PlaylistJobRepository(db)
        self.video_repo = PlaylistVideoRepository(db)
        self.artifact_repo = ArtifactRepository(db)
        self.notes_repo = NotesRepository(db)
        self.playlist_service = PlaylistService()

    async def create_job(self, request: CreateJobRequest) -> JobDetailResponse:
        # 1. Fetch Playlist Preview to validate and get all videos
        preview = await self.playlist_service.get_preview(request.playlist_input)
        options = request.options or GenerationOptions()

        # 2. Create PlaylistJob Entity
        job = PlaylistJob(
            playlist_id=preview.playlist_id,
            playlist_url=preview.playlist_url,
            playlist_title=request.title_override or preview.title,
            channel_name=preview.channel_name,
            status=JobStatus.QUEUED.value,
            current_stage="QUEUED",
            progress_percentage=0.0,
            options=options.model_dump(),
            total_videos=len(preview.videos),
            is_mock=preview.is_mock
        )
        try:
            created_job = self.job_repo.create(job)

            # 3. Create PlaylistVideo Entities in original position
            for v in preview.videos:
                status = VideoProcessingStatus.PENDING if v.is_available else VideoProcessingStatus.SKIPPED
                video_entity = PlaylistVideo(
                    job_id=created_job.id,
                    video_id=v.video_id,
                    original_position=v.original_position,
                    title=v.title,
                    channel_title=v.channel_title,
                    description=v.description,
                    thumbnail_url=v.thumbnail_url,
                    duration_seconds=v.duration_seconds,
                    video_url=v.video_url,
                    processing_status=status.value,
                    transcript_status=TranscriptStatus.NOT_FETCHED.value,
                    failure_reason=v.status_note
                )
                self.video_repo.create(video_entity)
        except Exception as e:
            self.db.rollback()
            logger.error("Failed creating job and videos in database: %s", e)
            raise

        # 4. Dispatch Job
        if settings.JOB_RUNNER == "celery":
            try:
                from app.workers.celery_app import execute_playlist_job
                execute_playlist_job.delay(created_job.id)
            except Exception as e:
                logger.warning(f"Failed to dispatch to Celery ({e}), falling back to inline runner")
                asyncio.create_task(run_playlist_job(created_job.id))
        else:
            asyncio.create_task(run_playlist_job(created_job.id))

        return self.get_job_detail(created_job.id)

    def get_job_detail(self, job_id: str) -> JobDetailResponse:
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise JobNotFoundException(job_id)

        videos = self.video_repo.list_by_job(job_id)
        video_schemas: List[VideoStatusSchema] = []

        for v in videos:
            has_notes = self.notes_repo.get_by_job_and_video(job_id, v.video_id) is not None
            dur_fmt = f"{v.duration_seconds // 60}:{v.duration_seconds % 60:02d}" if v.duration_seconds else "--:--"
            video_schemas.append(
                VideoStatusSchema(
                    video_id=v.video_id,
                    original_position=v.original_position,
                    title=v.title,
                    channel_title=v.channel_title,
                    thumbnail_url=v.thumbnail_url,
                    duration_formatted=dur_fmt,
                    status=VideoProcessingStatus(v.processing_status),
                    transcript_status=TranscriptStatus(v.transcript_status),
                    error_message=v.failure_reason,
                    has_notes=has_notes,
                    has_visual=False
                )
            )

        # Artifact lookup
        artifact = self.artifact_repo.get_by_job_id(job_id)
        artifact_schema = None
        if artifact:
            artifact_schema = ArtifactSchema(
                id=artifact.id,
                job_id=artifact.job_id,
                artifact_type=artifact.artifact_type,
                file_name=artifact.file_name,
                file_path=artifact.file_path,
                mime_type=artifact.mime_type,
                file_size_bytes=artifact.file_size_bytes,
                checksum_sha256=artifact.checksum_sha256,
                created_at=artifact.created_at,
                download_url=f"/api/v1/jobs/{job_id}/download",
                is_valid=artifact.is_valid
            )

        return JobDetailResponse(
            id=job.id,
            playlist_id=job.playlist_id,
            playlist_url=job.playlist_url,
            playlist_title=job.playlist_title,
            status=JobStatus(job.status),
            progress_percentage=job.progress_percentage,
            current_stage=job.current_stage,
            options=GenerationOptions(**job.options),
            total_videos=job.total_videos,
            completed_videos=job.completed_videos,
            failed_videos=job.failed_videos,
            skipped_videos=job.skipped_videos,
            error_summary=job.error_summary,
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at,
            artifact=artifact_schema,
            videos=video_schemas,
            is_mock=job.is_mock
        )

    def list_jobs(self, page: int = 1, page_size: int = 20) -> JobListResponse:
        skip = (page - 1) * page_size
        jobs, total = self.job_repo.list_jobs(skip=skip, limit=page_size)
        items = [self.get_job_detail(j.id) for j in jobs]
        return JobListResponse(
            jobs=items,
            total=total,
            page=page,
            page_size=page_size
        )

    async def retry_job(self, job_id: str) -> JobDetailResponse:
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise JobNotFoundException(job_id)

        # Reset failed videos to pending
        self.video_repo.reset_failed_for_retry(job_id)
        self.job_repo.update_status(job_id, JobStatus.QUEUED, stage="RETRY_QUEUED", progress=0.0)

        # Re-dispatch
        if settings.JOB_RUNNER == "celery":
            from app.workers.celery_app import execute_playlist_job
            execute_playlist_job.delay(job_id)
        else:
            asyncio.create_task(run_playlist_job(job_id))

        return self.get_job_detail(job_id)

    def cancel_job(self, job_id: str) -> JobDetailResponse:
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise JobNotFoundException(job_id)
        self.job_repo.update_status(job_id, JobStatus.CANCELLED, stage="CANCELLED")
        return self.get_job_detail(job_id)

