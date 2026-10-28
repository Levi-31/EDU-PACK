from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies import get_playlist_service
from app.domain.schemas.playlist import PlaylistPreviewRequest, PlaylistPreviewResponse
from app.services.playlist_service import PlaylistService
from app.core.exceptions import PlaylistScholarException

router = APIRouter(prefix="/playlists", tags=["Playlists"])


@router.post("/preview", response_model=PlaylistPreviewResponse)
async def preview_playlist(
    request: PlaylistPreviewRequest,
    service: PlaylistService = Depends(get_playlist_service)
):
    """
    Validates the YouTube playlist input, retrieves playlist metadata,
    and returns all ordered videos with thumbnail, channel, and duration.
    """
    try:
        return await service.get_preview(request.playlist_input)
    except PlaylistScholarException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to preview playlist: {str(e)}")

