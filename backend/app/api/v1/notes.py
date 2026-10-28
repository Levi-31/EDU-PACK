from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies import get_notes_service
from app.domain.schemas.notes import StructuredVideoNotes
from app.services.notes_service import NotesService

router = APIRouter(tags=["Notes"])


@router.get("/jobs/{job_id}/notes", response_model=List[StructuredVideoNotes])
def get_job_notes(
    job_id: str,
    service: NotesService = Depends(get_notes_service)
):
    """Returns all generated video notes for a job in exact playlist order"""
    return service.get_notes_for_job(job_id)


@router.get("/jobs/{job_id}/videos/{video_id}/notes", response_model=StructuredVideoNotes)
def get_video_notes(
    job_id: str,
    video_id: str,
    service: NotesService = Depends(get_notes_service)
):
    """Returns technical notes for a specific video"""
    notes = service.get_notes_for_video(job_id, video_id)
    if not notes:
        raise HTTPException(status_code=404, detail=f"Notes not found for video {video_id} in job {job_id}")
    return notes

