import logging
from typing import Optional
from app.core.config import settings
from app.domain.schemas.playlist import PlaylistPreviewResponse
from app.integrations.youtube.client import YouTubeClientInterface, OfficialYouTubeClient
from app.integrations.youtube.mock_client import MockYouTubeClient

logger = logging.getLogger(__name__)


class PlaylistService:
    def __init__(self, youtube_client: Optional[YouTubeClientInterface] = None):
        if youtube_client:
            self.youtube_client = youtube_client
        elif settings.YOUTUBE_API_KEY and settings.YOUTUBE_API_KEY.strip():
            self.youtube_client = OfficialYouTubeClient()
        else:
            self.youtube_client = MockYouTubeClient()

    async def get_preview(self, playlist_input: str) -> PlaylistPreviewResponse:
        return await self.youtube_client.fetch_playlist(playlist_input)

