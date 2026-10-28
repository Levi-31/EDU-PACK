import logging
from typing import Optional
from app.core.config import settings
from app.domain.schemas.playlist import PlaylistPreviewResponse
from app.integrations.youtube.client import YouTubeClientInterface, OfficialYouTubeClient
from app.integrations.youtube.mock_client import MockYouTubeClient
from app.integrations.youtube.parser import extract_playlist_id

logger = logging.getLogger(__name__)


class PlaylistService:
    def __init__(self, youtube_client: Optional[YouTubeClientInterface] = None):
        if youtube_client:
            self.youtube_client = youtube_client
        elif settings.DEMO_MODE or not settings.YOUTUBE_API_KEY or not settings.YOUTUBE_API_KEY.strip():
            self.youtube_client = MockYouTubeClient()
        else:
            self.youtube_client = OfficialYouTubeClient()

    async def get_preview(self, playlist_input: str) -> PlaylistPreviewResponse:
        try:
            playlist_id = extract_playlist_id(playlist_input)
            if "PL_DISTRIBUTED_SYSTEMS" in playlist_id or "PL_DEMO" in playlist_id:
                return await MockYouTubeClient().fetch_playlist(playlist_input)
        except Exception:
            pass

        return await self.youtube_client.fetch_playlist(playlist_input)
