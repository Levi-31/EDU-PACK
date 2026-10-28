import re
from urllib.parse import urlparse, parse_qs
from typing import Optional
from app.core.exceptions import InvalidPlaylistException

# YouTube playlist ID pattern: typically starts with PL, UU, FL, RD, OLAK5uy_, etc. (12 to 64 chars)
PLAYLIST_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]{10,64}$")


def extract_playlist_id(input_str: str) -> str:
    """
    Extracts and validates a YouTube playlist ID from:
    - Raw ID: 'PL1234567890abcdef'
    - Standard URL: 'https://www.youtube.com/playlist?list=PL1234567890abcdef'
    - Watch URL with playlist: 'https://www.youtube.com/watch?v=VIDEO_ID&list=PL1234567890abcdef'
    - Shortened URL: 'https://youtu.be/watch?list=PL1234567890abcdef'
    """
    if not input_str or not input_str.strip():
        raise InvalidPlaylistException("Playlist input cannot be empty.")

    clean_input = input_str.strip()

    # Check if raw playlist ID
    if PLAYLIST_ID_REGEX.match(clean_input) and not clean_input.startswith("http"):
        return clean_input

    # Parse as URL
    try:
        parsed = urlparse(clean_input)
        if not parsed.scheme:
            # Maybe user provided youtube.com/playlist?list=... without protocol
            parsed = urlparse("https://" + clean_input)

        qs = parse_qs(parsed.query)
        if "list" in qs and qs["list"]:
            playlist_id = qs["list"][0]
            if PLAYLIST_ID_REGEX.match(playlist_id):
                return playlist_id
    except Exception:
        pass

    raise InvalidPlaylistException(
        f"Unable to extract a valid YouTube playlist ID from input: '{input_str}'. "
        "Please provide a valid YouTube playlist URL or ID (e.g., 'https://www.youtube.com/playlist?list=PL...')."
    )


def construct_playlist_url(playlist_id: str) -> str:
    return f"https://www.youtube.com/playlist?list={playlist_id}"


def construct_video_url(video_id: str, timestamp_seconds: Optional[float] = None) -> str:
    base = f"https://www.youtube.com/watch?v={video_id}"
    if timestamp_seconds is not None and timestamp_seconds > 0:
        return f"{base}&t={int(timestamp_seconds)}s"
    return base
