import pytest
from app.integrations.youtube.parser import extract_playlist_id, construct_playlist_url, construct_video_url
from app.integrations.youtube.client import parse_iso8601_duration, format_duration
from app.core.exceptions import InvalidPlaylistException


def test_extract_playlist_id_from_raw_id():
    raw_id = "PL1234567890abcdef"
    assert extract_playlist_id(raw_id) == raw_id


def test_extract_playlist_id_from_standard_url():
    url = "https://www.youtube.com/playlist?list=PLab78cdEFG1234"
    assert extract_playlist_id(url) == "PLab78cdEFG1234"


def test_extract_playlist_id_from_watch_url():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLMC9POtZKhMR_123456"
    assert extract_playlist_id(url) == "PLMC9POtZKhMR_123456"


def test_extract_playlist_id_invalid_raises():
    with pytest.raises(InvalidPlaylistException):
        extract_playlist_id("not-a-valid-playlist-id!@#")

    with pytest.raises(InvalidPlaylistException):
        extract_playlist_id("")


def test_construct_video_url_with_and_without_timestamp():
    # Without timestamp
    assert construct_video_url("dQw4w9WgXcQ") == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    # With timestamp
    assert construct_video_url("dQw4w9WgXcQ", 212.5) == "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=212s"


def test_parse_iso8601_duration():
    assert parse_iso8601_duration("PT1H2M3S") == 3723
    assert parse_iso8601_duration("PT25M10S") == 1510
    assert parse_iso8601_duration("PT45S") == 45
    assert parse_iso8601_duration("") == 0


def test_format_duration():
    assert format_duration(3723) == "1:02:03"
    assert format_duration(1510) == "25:10"
    assert format_duration(45) == "00:45"
