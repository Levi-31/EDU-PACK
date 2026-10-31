import asyncio
import logging
from typing import Optional
from app.core.config import settings
from app.domain.enums import JobStatus, VideoProcessingStatus, TranscriptStatus
from app.domain.schemas.playlist import GenerationOptions
from app.agents.state import PlaylistGraphState, VideoGraphItem
from app.agents.graph import PlaylistWorkflowOrchestrator
from app.integrations.transcripts.youtube_transcript import YouTubeTranscriptProvider
from app.integrations.transcripts.mock_provider import MockTranscriptProvider
from app.integrations.openai.client import OfficialOpenAIClient
from app.integrations.openai.mock_client import MockOpenAIClient
from app.services.pdf_service import PDFService
from app.workers.event_bus import event_bus
from app.db.session import SessionLocal
from app.db.repositories.job_repository import PlaylistJobRepository
from app.db.repositories.video_repository import PlaylistVideoRepository
from app.db.repositories.transcript_repository import TranscriptRepository
from app.db.repositories.notes_repository import NotesRepository

logger = logging.getLogger(__name__)


async def run_playlist_job(job_id: str):
    """
    Executes the complete LangGraph workflow for a given job_id.
    Persists transcript, notes, visuals, and final PDF artifacts to the database.
    """
    db = SessionLocal()
    try:
        job_repo = PlaylistJobRepository(db)
        video_repo = PlaylistVideoRepository(db)
        transcript_repo = TranscriptRepository(db)
        notes_repo = NotesRepository(db)

        job = job_repo.get_by_id(job_id)
        if not job:
            logger.error(f"Job {job_id} not found in database.")
            return

        videos = video_repo.list_by_job(job_id)
        if not videos:
            job_repo.update_status(job_id, JobStatus.FAILED, error_summary="No videos found in playlist.")
            return

        # Prepare Graph State
        options = GenerationOptions(**job.options)
        video_items = [
            VideoGraphItem(
                video_id=v.video_id,
                original_position=v.original_position,
                title=v.title,
                channel_title=v.channel_title,
                description=v.description,
                duration_seconds=v.duration_seconds,
                thumbnail_url=v.thumbnail_url,
                video_url=v.video_url,
                is_available=(v.processing_status != "SKIPPED")
            )
            for v in videos
        ]

        initial_state = PlaylistGraphState(
            job_id=job_id,
            playlist_id=job.playlist_id,
            playlist_title=job.playlist_title,
            playlist_url=job.playlist_url,
            channel_name=job.channel_name,
            options=options,
            videos=video_items,
            current_stage="STARTING",
            overall_progress=0.0
        )

        # Select Providers (Mock vs Official)
        is_mock_run = (
            getattr(job, "is_mock", False)
            or not settings.OPENAI_API_KEY
            or not settings.OPENAI_API_KEY.strip()
            or "PL_DISTRIBUTED_SYSTEMS" in str(job.playlist_id)
            or "PL_DEMO" in str(job.playlist_id)
        )

        if is_mock_run:
            llm_client = MockOpenAIClient()
            transcript_provider = MockTranscriptProvider()
        else:
            llm_client = OfficialOpenAIClient()
            transcript_provider = YouTubeTranscriptProvider()

        pdf_service = PDFService()

        # Define Event Callback for Graph
        async def event_callback(job_id: str, stage: str, message: str, progress: float, video_id: Optional[str] = None):
            await event_bus.publish(
                job_id=job_id,
                stage=stage,
                message=message,
                progress=progress,
                video_id=video_id
            )

        orchestrator = PlaylistWorkflowOrchestrator(
            transcript_provider=transcript_provider,
            llm_client=llm_client,
            pdf_service=pdf_service,
            event_callback=event_callback
        )

        # Run Workflow
        final_state = await orchestrator.run(initial_state)

        # Persist Video Results into DB
        completed_count = 0
        failed_count = 0
        skipped_count = 0

        for v_item in final_state.videos:
            if v_item.transcript and v_item.transcript.segments:
                transcript_repo.upsert_transcript(
                    job_id=job_id,
                    video_id=v_item.video_id,
                    source=v_item.transcript.source,
                    language=v_item.transcript.language,
                    status=v_item.transcript.status.value,
                    segments_json=[s.model_dump() for s in v_item.transcript.segments],
                    raw_text=v_item.transcript.get_text(),
                    error_message=v_item.transcript.error_message
                )

            if v_item.notes:
                if v_item.visual and not v_item.notes.visual:
                    v_item.notes.visual = v_item.visual
                notes_repo.upsert_notes(
                    job_id=job_id,
                    video_id=v_item.video_id,
                    notes_json=v_item.notes.model_dump(),
                    model_id=settings.OPENAI_TEXT_MODEL,
                    review_status=v_item.review.status if v_item.review else "APPROVED",
                    review_findings_json=v_item.review.model_dump() if v_item.review else None
                )
                completed_count += 1
            elif v_item.status == VideoProcessingStatus.SKIPPED:
                skipped_count += 1
            else:
                failed_count += 1

            video_repo.update_video_status(
                job_id=job_id,
                video_id=v_item.video_id,
                status=v_item.status,
                transcript_status=v_item.transcript.status if v_item.transcript else None,
                failure_reason=v_item.failure_reason
            )

        # Determine Final Job Status
        if completed_count == len(final_state.videos):
            final_job_status = JobStatus.COMPLETED
        elif completed_count > 0:
            final_job_status = JobStatus.PARTIAL_SUCCESS
        else:
            final_job_status = JobStatus.FAILED

        job_repo.update_status(
            job_id=job_id,
            status=final_job_status,
            stage="FINISHED",
            progress=100.0,
            error_summary=final_state.error_summary,
            completed_videos=completed_count,
            failed_videos=failed_count,
            skipped_videos=skipped_count
        )

    except Exception as e:
        logger.error(f"Fatal error in run_playlist_job {job_id}: {e}", exc_info=True)
        job_repo = PlaylistJobRepository(db)
        job_repo.update_status(
            job_id=job_id,
            status=JobStatus.FAILED,
            stage="FAILED",
            progress=100.0,
            error_summary=str(e)
        )
        await event_bus.publish(
            job_id=job_id,
            stage=JobStatus.FAILED.value,
            message=f"Job terminated with error: {str(e)}",
            progress=100.0
        )
    finally:
        db.close()
