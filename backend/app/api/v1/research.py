from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.exceptions import PlaylistScholarException
from app.domain.schemas.research_module import (
    CreateResearchJobRequest,
    ResearchJobDetailResponse,
    ResearchJobListResponse,
)
from app.modules.research.research_service import ResearchService

router = APIRouter(prefix="/research", tags=["Research"])


def get_research_service(db: Session = Depends(get_db)) -> ResearchService:
    return ResearchService(db)


@router.post("/generate", response_model=ResearchJobDetailResponse, status_code=201)
async def generate_research(
    request: CreateResearchJobRequest,
    service: ResearchService = Depends(get_research_service)
):
    """
    Creates and initiates an agentic research job using Levi-31/Research-Tool.
    Executes Router -> Research -> Orchestrator -> Parallel Workers -> Reducer -> Image Planning & Generation.
    """
    try:
        return await service.create_job(request)
    except PlaylistScholarException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate research: {str(e)}")


@router.get("", response_model=ResearchJobListResponse)
def list_research_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ResearchService = Depends(get_research_service)
):
    """Returns paginated history of research jobs."""
    return service.list_jobs(page=page, page_size=page_size)


@router.get("/{job_id}", response_model=ResearchJobDetailResponse)
def get_research_job(
    job_id: str,
    service: ResearchService = Depends(get_research_service)
):
    """Retrieves current research job progress, active stage, and routing decision."""
    try:
        return service.get_job_detail(job_id)
    except PlaylistScholarException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{job_id}/result", response_model=ResearchJobDetailResponse)
def get_research_result(
    job_id: str,
    service: ResearchService = Depends(get_research_service)
):
    """Retrieves the full completed research output including plan, evidence, markdown, images, and logs."""
    try:
        return service.get_job_detail(job_id)
    except PlaylistScholarException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{job_id}/download/markdown")
def download_markdown(
    job_id: str,
    service: ResearchService = Depends(get_research_service)
):
    """Downloads the consolidated research article as a Markdown (.md) document."""
    try:
        content, filename = service.get_markdown_file(job_id)
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except PlaylistScholarException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{job_id}/download/bundle")
def download_bundle(
    job_id: str,
    service: ResearchService = Depends(get_research_service)
):
    """Downloads a complete ZIP bundle containing the Markdown article and all generated image assets."""
    try:
        content, filename = service.get_bundle_file(job_id)
        return Response(
            content=content,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except PlaylistScholarException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{job_id}/download/pdf")
async def download_pdf(
    job_id: str,
    service: ResearchService = Depends(get_research_service)
):
    """Downloads the consolidated research article as a high-resolution publication PDF."""
    try:
        content, filename = await service.get_pdf_file(job_id)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except PlaylistScholarException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.get("/{job_id}/images/{filename}")
def get_research_image(
    job_id: str,
    filename: str,
    service: ResearchService = Depends(get_research_service)
):
    """Serves generated images to the frontend markdown renderer."""
    try:
        content, media_type = service.get_image_file(job_id, filename)
        return Response(
            content=content,
            media_type=media_type,
            headers={"Cache-Control": "public, max-age=86400"}
        )
    except PlaylistScholarException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

