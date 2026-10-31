from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models.video import PlaylistVideo
from app.db.repositories.base import BaseRepository
from app.domain.enums import VideoProcessingStatus, TranscriptStatus


class PlaylistVideoRepository(BaseRepository[PlaylistVideo]):
    def __init__(self, db: Session):
        super().__init__(PlaylistVideo, db)

    def get_by_job_and_video(self, job_id: str, video_id: str) -> Optional[PlaylistVideo]:
        return (
            self.db.query(PlaylistVideo)
            .filter(PlaylistVideo.job_id == job_id, PlaylistVideo.video_id == video_id)
            .first()
        )

    def list_by_job(self, job_id: str) -> List[PlaylistVideo]:
        return (
            self.db.query(PlaylistVideo)
            .filter(PlaylistVideo.job_id == job_id)
            .order_by(PlaylistVideo.original_position.asc())
            .all()
        )

    def update_video_status(
        self,
        job_id: str,
        video_id: str,
        status: VideoProcessingStatus,
        transcript_status: Optional[TranscriptStatus] = None,
        failure_reason: Optional[str] = None
    ) -> Optional[PlaylistVideo]:
        video = self.get_by_job_and_video(job_id, video_id)
        if not video:
            return None
        video.processing_status = status.value if hasattr(status, "value") else str(status)
        if transcript_status is not None:
            video.transcript_status = transcript_status.value if hasattr(transcript_status, "value") else str(transcript_status)
        if failure_reason is not None:
            video.failure_reason = failure_reason[:3900] if failure_reason else None
        if status in [VideoProcessingStatus.COMPLETED, VideoProcessingStatus.FAILED, VideoProcessingStatus.SKIPPED]:
            video.processed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(video)
        return video

    def reset_failed_for_retry(self, job_id: str) -> List[PlaylistVideo]:
        failed_videos = (
            self.db.query(PlaylistVideo)
            .filter(PlaylistVideo.job_id == job_id, PlaylistVideo.processing_status == "FAILED")
            .all()
        )
        for v in failed_videos:
            v.processing_status = "PENDING"
            v.failure_reason = None
            v.retry_count += 1
        self.db.commit()
        return failed_videos

