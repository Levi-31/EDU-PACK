from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.transcript import Transcript
from app.db.repositories.base import BaseRepository


class TranscriptRepository(BaseRepository[Transcript]):
    def __init__(self, db: Session):
        super().__init__(Transcript, db)

    def get_by_job_and_video(self, job_id: str, video_id: str) -> Optional[Transcript]:
        return (
            self.db.query(Transcript)
            .filter(Transcript.job_id == job_id, Transcript.video_id == video_id)
            .first()
        )

    def upsert_transcript(
        self,
        job_id: str,
        video_id: str,
        source: str,
        language: str,
        status: str,
        segments_json: list,
        raw_text: Optional[str] = None,
        transcript_hash: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Transcript:
        existing = self.get_by_job_and_video(job_id, video_id)
        if existing:
            existing.source = source
            existing.language = language
            existing.status = status
            existing.segments_json = segments_json
            existing.raw_text = raw_text
            existing.transcript_hash = transcript_hash
            existing.error_message = error_message
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            obj = Transcript(
                job_id=job_id,
                video_id=video_id,
                source=source,
                language=language,
                status=status,
                segments_json=segments_json,
                raw_text=raw_text,
                transcript_hash=transcript_hash,
                error_message=error_message
            )
            return self.create(obj)
