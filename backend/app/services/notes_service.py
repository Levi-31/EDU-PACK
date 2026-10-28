from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.repositories.notes_repository import NotesRepository
from app.domain.schemas.notes import StructuredVideoNotes


class NotesService:
    def __init__(self, db: Session):
        self.db = db
        self.notes_repo = NotesRepository(db)

    def get_notes_for_job(self, job_id: str) -> List[StructuredVideoNotes]:
        models = self.notes_repo.list_by_job(job_id)
        result: List[StructuredVideoNotes] = []
        for m in models:
            try:
                result.append(StructuredVideoNotes(**m.notes_json))
            except Exception:
                pass
        return result

    def get_notes_for_video(self, job_id: str, video_id: str) -> Optional[StructuredVideoNotes]:
        model = self.notes_repo.get_by_job_and_video(job_id, video_id)
        if model and model.notes_json:
            return StructuredVideoNotes(**model.notes_json)
        return None
