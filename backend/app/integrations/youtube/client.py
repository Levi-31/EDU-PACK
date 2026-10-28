import re
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict, Any
import httpx
from app.core.config import settings
from app.core.exceptions import PlaylistNotFoundException, InvalidPlaylistException
from app.domain.schemas.playlist import PlaylistItemPreview, PlaylistPreviewResponse
from app.integrations.youtube.parser import extract_playlist_id, construct_playlist_url, construct_video_url


def parse_iso8601_duration(duration_str: str) -> int:
    """Parses ISO 8601 duration string (e.g. PT1H15M30S, PT4M12S) to seconds"""
    if not duration_str or not duration_str.startswith("PT"):
        return 0
    pattern = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")
    match = pattern.match(duration_str)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def format_duration(seconds: int) -> str:
    if seconds <= 0:
        return "00:00"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


class YouTubeClientInterface(ABC):
    @abstractmethod
    async def fetch_playlist(self, playlist_input: str) -> PlaylistPreviewResponse:
        pass


class OfficialYouTubeClient(YouTubeClientInterface):
    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.YOUTUBE_API_KEY
        if not self.api_key:
            raise InvalidPlaylistException("YouTube API Key is missing. Set YOUTUBE_API_KEY or enable DEMO_MODE.")

    async def fetch_playlist(self, playlist_input: str) -> PlaylistPreviewResponse:
        playlist_id = extract_playlist_id(playlist_input)
        if "PL_DISTRIBUTED_SYSTEMS" in playlist_id or "PL_DEMO" in playlist_id:
            from app.integrations.youtube.mock_client import MockYouTubeClient
            return await MockYouTubeClient().fetch_playlist(playlist_input)

        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Fetch Playlist Metadata
            meta_resp = await client.get(
                f"{self.BASE_URL}/playlists",
                params={
                    "part": "snippet,contentDetails",
                    "id": playlist_id,
                    "key": self.api_key,
                }
            )
            if meta_resp.status_code == 404 or not meta_resp.json().get("items"):
                raise PlaylistNotFoundException(f"Playlist {playlist_id} not found or is private.")
            if meta_resp.status_code != 200:
                raise InvalidPlaylistException(f"YouTube API returned error: {meta_resp.text}")

            meta_item = meta_resp.json()["items"][0]
            snippet = meta_item.get("snippet", {})
            title = snippet.get("title", "Untitled Playlist")
            description = snippet.get("description", "")
            channel_name = snippet.get("channelTitle", "")
            thumbnails = snippet.get("thumbnails", {})
            thumb_url = (
                thumbnails.get("maxres", {}).get("url")
                or thumbnails.get("high", {}).get("url")
                or thumbnails.get("default", {}).get("url")
            )

            # 2. Paginate over all PlaylistItems
            all_items: List[Dict[str, Any]] = []
            next_page_token = None

            while True:
                params = {
                    "part": "snippet,contentDetails,status",
                    "playlistId": playlist_id,
                    "maxResults": 50,
                    "key": self.api_key,
                }
                if next_page_token:
                    params["pageToken"] = next_page_token

                items_resp = await client.get(f"{self.BASE_URL}/playlistItems", params=params)
                if items_resp.status_code != 200:
                    break
                data = items_resp.json()
                items = data.get("items", [])
                all_items.extend(items)
                next_page_token = data.get("nextPageToken")
                if not next_page_token:
                    break

            # 3. Retrieve video durations in batches of 50
            video_ids = [
                item.get("snippet", {}).get("resourceId", {}).get("videoId")
                for item in all_items
                if item.get("snippet", {}).get("resourceId", {}).get("videoId")
            ]
            video_durations: Dict[str, int] = {}

            for i in range(0, len(video_ids), 50):
                batch_ids = video_ids[i:i + 50]
                if not batch_ids:
                    continue
                v_resp = await client.get(
                    f"{self.BASE_URL}/videos",
                    params={
                        "part": "contentDetails",
                        "id": ",".join(batch_ids),
                        "key": self.api_key,
                    }
                )
                if v_resp.status_code == 200:
                    for v_item in v_resp.json().get("items", []):
                        vid = v_item["id"]
                        iso_dur = v_item.get("contentDetails", {}).get("duration", "")
                        video_durations[vid] = parse_iso8601_duration(iso_dur)

            # 4. Construct ordered PlaylistItemPreview list
            ordered_videos: List[PlaylistItemPreview] = []
            available_count = 0

            for idx, item in enumerate(all_items):
                item_snippet = item.get("snippet", {})
                res_id = item_snippet.get("resourceId", {})
                vid = res_id.get("videoId")
                if not vid:
                    continue

                v_title = item_snippet.get("title", "")
                is_available = True
                status_note = None

                # Detect deleted or private videos
                if v_title in ["Private video", "Deleted video"] or not item_snippet.get("thumbnails"):
                    is_available = False
                    status_note = f"Video is {v_title.lower()} or inaccessible"

                v_channel = item_snippet.get("videoOwnerChannelTitle") or item_snippet.get("channelTitle")
                v_desc = item_snippet.get("description", "")
                v_thumbs = item_snippet.get("thumbnails", {})
                v_thumb_url = (
                    v_thumbs.get("high", {}).get("url")
                    or v_thumbs.get("medium", {}).get("url")
                    or v_thumbs.get("default", {}).get("url")
                )
                duration_sec = video_durations.get(vid, 0)
                duration_fmt = format_duration(duration_sec)

                if is_available:
                    available_count += 1

                ordered_videos.append(
                    PlaylistItemPreview(
                        video_id=vid,
                        original_position=idx,
                        title=v_title,
                        channel_title=v_channel,
                        description=v_desc,
                        thumbnail_url=v_thumb_url,
                        duration_seconds=duration_sec,
                        duration_formatted=duration_fmt,
                        video_url=construct_video_url(vid),
                        is_available=is_available,
                        status_note=status_note
                    )
                )

            return PlaylistPreviewResponse(
                playlist_id=playlist_id,
                title=title,
                description=description,
                channel_name=channel_name,
                thumbnail_url=thumb_url,
                total_videos=len(ordered_videos),
                available_videos_count=available_count,
                playlist_url=construct_playlist_url(playlist_id),
                videos=ordered_videos,
                is_mock=False
            )

