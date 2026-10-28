import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories.artifact_repository import ArtifactRepository
from app.db.repositories.job_repository import PlaylistJobRepository
from app.domain.enums import ArtifactType

router = APIRouter(tags=["Artifacts"])


@router.api_route("/jobs/{job_id}/download", methods=["GET", "HEAD"])
def download_pdf(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Downloads the compiled PDF study guide for a finished job.
    Includes proper Content-Disposition header with safe filename.
    """
    job_repo = PlaylistJobRepository(db)
    job = job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    artifact_repo = ArtifactRepository(db)
    artifact = artifact_repo.get_by_job_id(job_id, artifact_type=ArtifactType.PDF_NOTES.value)
    if not artifact or not os.path.exists(artifact.file_path):
        raise HTTPException(status_code=404, detail="PDF artifact has not been compiled or is unavailable")

    return FileResponse(
        path=artifact.file_path,
        media_type="application/pdf",
        filename=artifact.file_name
    )

