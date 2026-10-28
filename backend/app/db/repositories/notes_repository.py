from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.notes import VideoNotes
from app.db.models.video import PlaylistVideo
from app.db.repositories.base import BaseRepository


class NotesRepository(BaseRepository[VideoNotes]):
    def __init__(self, db: Session):
        super().__init__(VideoNotes, db)

    def get_by_job_and_video(self, job_id: str, video_id: str) -> Optional[VideoNotes]:
        return (
            self.db.query(VideoNotes)
            .filter(VideoNotes.job_id == job_id, VideoNotes.video_id == video_id)
            .first()
        )

    def list_by_job(self, job_id: str) -> List[VideoNotes]:
        # Return notes joined and ordered by original video position
        return (
            self.db.query(VideoNotes)
            .join(PlaylistVideo, (PlaylistVideo.job_id == VideoNotes.job_id) & (PlaylistVideo.video_id == VideoNotes.video_id))
            .filter(VideoNotes.job_id == job_id)
            .order_by(PlaylistVideo.original_position.asc())
            .all()
        )

    def upsert_notes(
        self,
        job_id: str,
        video_id: str,
        notes_json: dict,
        model_id: str,
        prompt_version: str = "v1",
        review_status: str = "APPROVED",
        review_findings_json: Optional[dict] = None
    ) -> VideoNotes:
        existing = self.get_by_job_and_video(job_id, video_id)
        if existing:
            existing.notes_json = notes_json
            existing.model_id = model_id
            existing.prompt_version = prompt_version
            existing.review_status = review_status
            existing.review_findings_json = review_findings_json
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            obj = VideoNotes(
                job_id=job_id,
                video_id=video_id,
                notes_json=notes_json,
                model_id=model_id,
                prompt_version=prompt_version,
                review_status=review_status,
                review_findings_json=review_findings_json
            )
            return self.create(obj)
