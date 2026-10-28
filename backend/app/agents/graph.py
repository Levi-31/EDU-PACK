import asyncio
import logging
from typing import List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END

from app.core.config import settings
from app.core.exceptions import PDFGenerationException
from app.domain.enums import JobStatus, VideoProcessingStatus, TranscriptStatus
from app.agents.state import PlaylistGraphState, VideoGraphItem
from app.agents.transcript_agent import TranscriptProcessingAgent
from app.agents.notes_agent import TechnicalNotesAgent
from app.agents.visual_agent import VisualDiagramAgent
from app.agents.review_agent import NotesReviewAgent
from app.integrations.transcripts.provider import TranscriptProvider
from app.integrations.openai.client import OpenAIClientInterface

logger = logging.getLogger(__name__)


class PlaylistWorkflowOrchestrator:
    """
    Stateful workflow coordinator built with LangGraph.
    Coordinates per-video transcript retrieval, technical note generation,
    conditional visual synthesis, grounded review critique, and ordered PDF compilation.
    """

    def __init__(
        self,
        transcript_provider: TranscriptProvider,
        llm_client: OpenAIClientInterface,
        pdf_service: Any = None,
        event_callback: Optional[Any] = None
    ):
        self.transcript_provider = transcript_provider
        self.llm_client = llm_client
        self.pdf_service = pdf_service
        self.event_callback = event_callback

        self.transcript_agent = TranscriptProcessingAgent()
        self.notes_agent = TechnicalNotesAgent(llm_client)
        self.visual_agent = VisualDiagramAgent(llm_client)
        self.review_agent = NotesReviewAgent(llm_client)

        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(PlaylistGraphState)

        builder.add_node("plan_processing", self._plan_node)
        builder.add_node("process_all_videos", self._process_videos_node)
        builder.add_node("compile_and_validate_pdf", self._compile_pdf_node)

        builder.add_edge(START, "plan_processing")
        builder.add_edge("plan_processing", "process_all_videos")
        builder.add_edge("process_all_videos", "compile_and_validate_pdf")
        builder.add_edge("compile_and_validate_pdf", END)

        return builder.compile()

    async def _emit_event(self, job_id: str, stage: str, message: str, progress: float, video_id: Optional[str] = None):
        if self.event_callback:
            try:
                await self.event_callback(job_id=job_id, stage=stage, message=message, progress=progress, video_id=video_id)
            except Exception as e:
                logger.warning(f"Error in event_callback: {e}")

    async def _plan_node(self, state: PlaylistGraphState) -> Dict[str, Any]:
        """Coordinator Agent: plans the per-video work and sets initial progress"""
        logger.info(f"Coordinator planning processing for job {state.job_id} ({len(state.videos)} videos)")
        await self._emit_event(
            job_id=state.job_id,
            stage="PLANNING",
            message=f"Planning processing pipeline for {len(state.videos)} videos in original playlist sequence.",
            progress=5.0
        )
        return {
            "current_stage": "PLANNING",
            "overall_progress": 5.0
        }

    async def _process_single_video(self, item: VideoGraphItem, state: PlaylistGraphState) -> VideoGraphItem:
        """Processes one video through transcript, notes, visuals, and review agents"""
        vid = item.video_id
        pos = item.original_position + 1
        logger.info(f"Processing video {pos}/{len(state.videos)}: {item.title} ({vid})")

        if not item.is_available:
            item.status = VideoProcessingStatus.SKIPPED
            item.failure_reason = item.failure_reason or "Video is private, deleted, or unavailable on YouTube."
            return item

        try:
            # 1. Retrieve Transcript
            item.status = VideoProcessingStatus.FETCHING_TRANSCRIPT
            await self._emit_event(
                job_id=state.job_id,
                stage="FETCHING_TRANSCRIPTS",
                message=f"Acquiring transcript for [{pos}/{len(state.videos)}] '{item.title[:40]}...'",
                progress=state.overall_progress,
                video_id=vid
            )

            transcript = await self.transcript_provider.get_transcript(
                video_id=vid,
                language=state.options.transcript_language
            )
            item.transcript = transcript

            # Evaluate transcript quality
            is_valid, quality_msg = self.transcript_agent.evaluate_quality(transcript)
            if not is_valid:
                item.status = VideoProcessingStatus.TRANSCRIPT_FAILED
                item.failure_reason = quality_msg
                logger.warning(f"Transcript unavailable for {vid}: {quality_msg}")
                return item

            # 2. Generate Technical Notes
            item.status = VideoProcessingStatus.GENERATING_NOTES
            await self._emit_event(
                job_id=state.job_id,
                stage="GENERATING_NOTES",
                message=f"Generating structured technical notes for [{pos}/{len(state.videos)}] '{item.title[:40]}...'",
                progress=state.overall_progress,
                video_id=vid
            )

            video_meta = {
                "video_id": vid,
                "title": item.title,
                "channel_title": item.channel_title,
                "duration_seconds": item.duration_seconds,
                "thumbnail_url": item.thumbnail_url,
                "video_url": item.video_url,
                "original_position": item.original_position
            }
            notes = await self.notes_agent.generate_notes_for_video(
                video_metadata=video_meta,
                transcript=transcript,
                detail_level=state.options.detail_level.value
            )
            item.notes = notes

            # 3. Conditional Visuals
            if state.options.enable_visuals:
                item.status = VideoProcessingStatus.GENERATING_VISUALS
                visual = await self.visual_agent.evaluate_and_generate(
                    notes=notes,
                    enable_visuals=state.options.enable_visuals
                )
                item.visual = visual

            # 4. Review & Critic
            item.status = VideoProcessingStatus.REVIEWING
            review_report, needs_revision = await self.review_agent.review(
                notes=notes,
                transcript=transcript,
                current_revision_count=item.revision_attempts
            )
            item.review = review_report

            if needs_revision:
                item.revision_attempts += 1
                logger.info(f"Applying bounded revision cycle for {vid} (attempt {item.revision_attempts})")
                notes = await self.notes_agent.generate_notes_for_video(
                    video_metadata=video_meta,
                    transcript=transcript,
                    detail_level=state.options.detail_level.value
                )
                item.notes = notes

            item.status = VideoProcessingStatus.COMPLETED
            return item

        except Exception as e:
            logger.error(f"Error processing video {vid}: {e}", exc_info=True)
            item.status = VideoProcessingStatus.FAILED
            item.failure_reason = str(e)
            return item

    async def _process_videos_node(self, state: PlaylistGraphState) -> Dict[str, Any]:
        """Processes all playlist videos with bounded concurrency while preserving original sequence"""
        concurrency = min(settings.MAX_CONCURRENT_LLM_REQUESTS, 4)
        semaphore = asyncio.Semaphore(concurrency)
        total_videos = len(state.videos)

        processed_videos: List[VideoGraphItem] = list(state.videos)

        async def worker(idx: int, item: VideoGraphItem):
            async with semaphore:
                res = await self._process_single_video(item, state)
                processed_videos[idx] = res
                
                # Update progress proportionally (between 10% and 80%)
                done_count = sum(1 for v in processed_videos if v.status in [
                    VideoProcessingStatus.COMPLETED,
                    VideoProcessingStatus.FAILED,
                    VideoProcessingStatus.SKIPPED,
                    VideoProcessingStatus.TRANSCRIPT_FAILED
                ])
                calc_progress = 10.0 + (done_count / max(total_videos, 1)) * 70.0
                state.overall_progress = round(calc_progress, 1)

                await self._emit_event(
                    job_id=state.job_id,
                    stage="PROCESSING_VIDEOS",
                    message=f"Completed processing {done_count} of {total_videos} videos.",
                    progress=state.overall_progress
                )

        tasks = [worker(i, v) for i, v in enumerate(state.videos)]
        await asyncio.gather(*tasks)

        # Ensure processed_videos strictly preserves original position
        processed_videos.sort(key=lambda x: x.original_position)

        return {
            "videos": processed_videos,
            "current_stage": "PROCESSING_COMPLETE",
            "overall_progress": 80.0
        }

    async def _compile_pdf_node(self, state: PlaylistGraphState) -> Dict[str, Any]:
        """Compiles the final PDF document and validates the artifact"""
        logger.info(f"Compiling PDF for job {state.job_id}")
        await self._emit_event(
            job_id=state.job_id,
            stage="RENDERING_PDF",
            message="Assembling notes into high-fidelity PDF with clickable YouTube hyperlinks.",
            progress=85.0
        )

        if not self.pdf_service:
            logger.warning("No PDF service attached to orchestrator.")
            return {"current_stage": "PDF_SKIPPED"}

        try:
            artifact = await self.pdf_service.compile_playlist_pdf(
                job_id=state.job_id,
                playlist_title=state.playlist_title,
                playlist_url=state.playlist_url,
                channel_name=state.channel_name,
                videos=state.videos,
                options=state.options
            )

            # Determine final job status
            completed_notes = sum(1 for v in state.videos if v.notes is not None)
            total = len(state.videos)
            final_status = JobStatus.COMPLETED if completed_notes == total else (
                JobStatus.PARTIAL_SUCCESS if completed_notes > 0 else JobStatus.FAILED
            )

            await self._emit_event(
                job_id=state.job_id,
                stage="COMPLETED",
                message=f"Compilation complete: {completed_notes}/{total} video chapters generated. PDF ready for download.",
                progress=100.0
            )

            return {
                "pdf_artifact_path": artifact.file_path,
                "pdf_artifact_id": artifact.id,
                "current_stage": final_status.value,
                "overall_progress": 100.0
            }
        except Exception as e:
            logger.error(f"PDF compilation failed: {e}", exc_info=True)
            await self._emit_event(
                job_id=state.job_id,
                stage="FAILED",
                message=f"PDF rendering failed: {str(e)}",
                progress=state.overall_progress
            )
            return {
                "error_summary": str(e),
                "current_stage": "FAILED"
            }

    async def run(self, initial_state: PlaylistGraphState) -> PlaylistGraphState:
        result = await self.graph.ainvoke(initial_state)
        if isinstance(result, dict):
            return PlaylistGraphState(**result)
        return result
