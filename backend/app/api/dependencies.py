from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.playlist_service import PlaylistService
from app.services.job_service import JobService
from app.services.notes_service import NotesService
from app.services.pdf_service import PDFService


def get_playlist_service() -> PlaylistService:
    return PlaylistService()


def get_job_service(db: Session = Depends(get_db)) -> JobService:
    return JobService(db)


def get_notes_service(db: Session = Depends(get_db)) -> NotesService:
    return NotesService(db)


def get_pdf_service() -> PDFService:
    return PDFService()
