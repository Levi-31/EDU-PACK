import re
from enum import Enum
from urllib.parse import urlparse, parse_qs
from typing import Optional, NamedTuple
from app.core.exceptions import InvalidPlaylistException

# YouTube video IDs are exactly 11 characters (base64url)
VIDEO_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]{11}$")

# YouTube playlist IDs typically start with PL, UU, FL, RD, OLAK5uy_, etc. (10 to 64 chars)
PLAYLIST_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]{10,64}$")

VALID_YOUTUBE_DOMAINS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "gaming.youtube.com",
    "youtu.be",
    "www.youtu.be"
}


class YouTubeSourceType(str, Enum):
    VIDEO = "video"
    PLAYLIST = "playlist"


class ParsedYouTubeTarget(NamedTuple):
    source_type: YouTubeSourceType
    target_id: str
    normalized_url: str
    video_id: Optional[str] = None
    playlist_id: Optional[str] = None


def parse_youtube_target(input_str: str) -> ParsedYouTubeTarget:
    """
    Parses and validates any YouTube video or playlist input string.
    Supports:
    - Individual videos:
        * https://www.youtube.com/watch?v=VIDEO_ID
        * https://youtu.be/VIDEO_ID
        * https://www.youtube.com/shorts/VIDEO_ID
        * https://www.youtube.com/embed/VIDEO_ID
        * Raw 11-char video ID: 'fMHGSx8B9gs'
    - Playlists:
        * https://www.youtube.com/playlist?list=PLAYLIST_ID
        * https://www.youtube.com/watch?v=VIDEO_ID&list=PLAYLIST_ID (prefers playlist)
        * Raw playlist ID: 'PL_DISTRIBUTED_SYSTEMS_2026'

    Raises actionable InvalidPlaylistException on invalid, malformed, or unrelated URLs.
    """
    if not input_str or not input_str.strip():
        raise InvalidPlaylistException("YouTube URL or ID cannot be empty.")

    clean_input = input_str.strip()

    # 1. Check if raw ID
    if not clean_input.startswith("http://") and not clean_input.startswith("https://") and "/" not in clean_input:
        # Check raw video ID first (11 chars)
        if VIDEO_ID_REGEX.match(clean_input) and not clean_input.startswith("PL"):
            return ParsedYouTubeTarget(
                source_type=YouTubeSourceType.VIDEO,
                target_id=clean_input,
                normalized_url=f"https://www.youtube.com/watch?v={clean_input}",
                video_id=clean_input
            )
        # Check raw playlist ID
        if PLAYLIST_ID_REGEX.match(clean_input):
            return ParsedYouTubeTarget(
                source_type=YouTubeSourceType.PLAYLIST,
                target_id=clean_input,
                normalized_url=f"https://www.youtube.com/playlist?list={clean_input}",
                playlist_id=clean_input
            )

    # 2. Parse as URL
    try:
        url_to_parse = clean_input
        if not url_to_parse.startswith("http://") and not url_to_parse.startswith("https://"):
            url_to_parse = "https://" + url_to_parse

        parsed = urlparse(url_to_parse)
        domain = (parsed.hostname or "").lower()

        # Reject foreign domains
        if domain not in VALID_YOUTUBE_DOMAINS:
            raise InvalidPlaylistException(
                f"Invalid YouTube URL domain '{domain}'. Please provide a valid YouTube link "
                "(e.g., 'https://www.youtube.com/watch?v=...' or 'https://www.youtube.com/playlist?list=...')."
            )

        qs = parse_qs(parsed.query)
        path = parsed.path.rstrip("/")

        # A. Playlist checking
        # Explicit playlist path e.g. /playlist?list=PL...
        if path == "/playlist" and "list" in qs and qs["list"]:
            pl_id = qs["list"][0]
            if PLAYLIST_ID_REGEX.match(pl_id):
                return ParsedYouTubeTarget(
                    source_type=YouTubeSourceType.PLAYLIST,
                    target_id=pl_id,
                    normalized_url=f"https://www.youtube.com/playlist?list={pl_id}",
                    playlist_id=pl_id
                )

        # /watch?v=...&list=...
        if "list" in qs and qs["list"]:
            pl_id = qs["list"][0]
            # Standard user expectation: when list parameter is attached to a watch URL, treat as complete playlist
            if PLAYLIST_ID_REGEX.match(pl_id):
                return ParsedYouTubeTarget(
                    source_type=YouTubeSourceType.PLAYLIST,
                    target_id=pl_id,
                    normalized_url=f"https://www.youtube.com/playlist?list={pl_id}",
                    playlist_id=pl_id,
                    video_id=qs.get("v", [None])[0]
                )

        # B. Video checking
        # 1. youtu.be/VIDEO_ID
        if "youtu.be" in domain:
            vid = path.lstrip("/")
            if VIDEO_ID_REGEX.match(vid):
                return ParsedYouTubeTarget(
                    source_type=YouTubeSourceType.VIDEO,
                    target_id=vid,
                    normalized_url=f"https://www.youtube.com/watch?v={vid}",
                    video_id=vid
                )

        # 2. /watch?v=VIDEO_ID
        if path == "/watch" and "v" in qs and qs["v"]:
            vid = qs["v"][0]
            if VIDEO_ID_REGEX.match(vid):
                return ParsedYouTubeTarget(
                    source_type=YouTubeSourceType.VIDEO,
                    target_id=vid,
                    normalized_url=f"https://www.youtube.com/watch?v={vid}",
                    video_id=vid
                )

        # 3. /shorts/VIDEO_ID
        if path.startswith("/shorts/"):
            vid = path.split("/shorts/")[1].split("/")[0]
            if VIDEO_ID_REGEX.match(vid):
                return ParsedYouTubeTarget(
                    source_type=YouTubeSourceType.VIDEO,
                    target_id=vid,
                    normalized_url=f"https://www.youtube.com/watch?v={vid}",
                    video_id=vid
                )

        # 4. /embed/VIDEO_ID or /v/VIDEO_ID
        for prefix in ("/embed/", "/v/"):
            if path.startswith(prefix):
                vid = path.split(prefix)[1].split("/")[0]
                if VIDEO_ID_REGEX.match(vid):
                    return ParsedYouTubeTarget(
                        source_type=YouTubeSourceType.VIDEO,
                        target_id=vid,
                        normalized_url=f"https://www.youtube.com/watch?v={vid}",
                        video_id=vid
                    )

    except InvalidPlaylistException:
        raise
    except Exception as e:
        raise InvalidPlaylistException(f"Failed to parse YouTube URL: {str(e)}")

    raise InvalidPlaylistException(
        f"Unable to recognize valid YouTube video or playlist format from input: '{input_str}'. "
        "Please provide a valid video link (e.g. 'https://www.youtube.com/watch?v=...') or "
        "playlist link (e.g. 'https://www.youtube.com/playlist?list=...')."
    )


def extract_playlist_id(input_str: str) -> str:
    """
    Backwards-compatible helper: extracts playlist ID or raises InvalidPlaylistException.
    """
    target = parse_youtube_target(input_str)
    if target.source_type == YouTubeSourceType.PLAYLIST and target.playlist_id:
        return target.playlist_id
    raise InvalidPlaylistException(
        f"Input '{input_str}' is a single YouTube video, not a playlist. "
        "Please use the unified target parser or submit a playlist URL."
    )


def extract_video_id(input_str: str) -> str:
    """
    Extracts single video ID or raises InvalidPlaylistException.
    """
    target = parse_youtube_target(input_str)
    if target.source_type == YouTubeSourceType.VIDEO and target.video_id:
        return target.video_id
    raise InvalidPlaylistException(
        f"Input '{input_str}' is a playlist or not a recognized single YouTube video."
    )



def construct_playlist_url(playlist_id: str) -> str:
    return f"https://www.youtube.com/playlist?list={playlist_id}"


def construct_video_url(video_id: str, timestamp_seconds: Optional[float] = None) -> str:
    base = f"https://www.youtube.com/watch?v={video_id}"
    if timestamp_seconds is not None and timestamp_seconds > 0:
        return f"{base}&t={int(timestamp_seconds)}s"
    return base
