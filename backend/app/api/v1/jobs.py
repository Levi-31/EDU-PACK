import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.api.dependencies import get_job_service
from app.domain.schemas.job import CreateJobRequest, JobDetailResponse, JobListResponse
from app.services.job_service import JobService
from app.workers.event_bus import event_bus
from app.core.exceptions import PlaylistScholarException

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("", response_model=JobDetailResponse, status_code=201)
async def create_job(
    request: CreateJobRequest,
    service: JobService = Depends(get_job_service)
):
    """Creates a new playlist notes generation job and starts background processing"""
    try:
        return await service.create_job(request)
    except PlaylistScholarException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@router.get("", response_model=JobListResponse)
def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: JobService = Depends(get_job_service)
):
    """Returns paginated list of generation jobs"""
    return service.list_jobs(page=page, page_size=page_size)


@router.get("/{job_id}", response_model=JobDetailResponse)
def get_job(
    job_id: str,
    service: JobService = Depends(get_job_service)
):
    """Retrieves current job status, progress percentage, and per-video state"""
    try:
        return service.get_job_detail(job_id)
    except PlaylistScholarException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{job_id}/events")
async def stream_job_events(job_id: str):
    """
    Server-Sent Events (SSE) endpoint providing live job progress updates.
    """
    async def event_generator():
        try:
            async for event in event_bus.subscribe(job_id):
                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/{job_id}/retry", response_model=JobDetailResponse)
async def retry_job(
    job_id: str,
    service: JobService = Depends(get_job_service)
):
    """Retries eligible failed video processing in the job"""
    try:
        return await service.retry_job(job_id)
    except PlaylistScholarException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{job_id}/cancel", response_model=JobDetailResponse)
def cancel_job(
    job_id: str,
    service: JobService = Depends(get_job_service)
):
    """Requests safe cancellation of a running job"""
    try:
        return service.cancel_job(job_id)
    except PlaylistScholarException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

