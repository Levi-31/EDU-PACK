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
        elif settings.YOUTUBE_API_KEY and settings.YOUTUBE_API_KEY.strip():
            self.youtube_client = OfficialYouTubeClient()
        else:
            self.youtube_client = MockYouTubeClient()

    async def get_preview(self, playlist_input: str) -> PlaylistPreviewResponse:
        playlist_id = ""
        try:
            playlist_id = extract_playlist_id(playlist_input)
            if "PL_DISTRIBUTED_SYSTEMS" in playlist_id or "PL_DEMO" in playlist_id:
                logger.info("Playlist ID '%s' identified as synthetic mock fixture.", playlist_id)
                return await MockYouTubeClient().fetch_playlist(playlist_input)
        except Exception:
            pass

        # If user has configured a YouTube API key, prioritize OfficialYouTubeClient
        if settings.YOUTUBE_API_KEY and settings.YOUTUBE_API_KEY.strip():
            try:
                logger.info("Fetching playlist metadata via OfficialYouTubeClient for input: %s", playlist_input)
                return await OfficialYouTubeClient().fetch_playlist(playlist_input)
            except Exception as e:
                logger.warning("Official YouTube API query failed: %s", e)
                # Only fallback to mock if the playlist input itself was not a valid public URL/ID
                if not playlist_id or "PL_DISTRIBUTED_SYSTEMS" in playlist_id:
                    return await MockYouTubeClient().fetch_playlist(playlist_input)
                raise

        return await self.youtube_client.fetch_playlist(playlist_input)
