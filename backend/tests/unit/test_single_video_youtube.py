import pytest
from app.integrations.youtube.parser import parse_youtube_target, extract_video_id, extract_playlist_id
from app.integrations.youtube.mock_client import MockYouTubeClient
from app.services.playlist_service import PlaylistService
from app.services.pdf_service import PDFService
from app.agents.state import VideoGraphItem
from app.domain.schemas.notes import StructuredVideoNotes, NoteTopicSection


def test_parse_youtube_target_single_video():
    # 1. Standard watch URL
    target = parse_youtube_target("https://www.youtube.com/watch?v=fMHGSx8B9gs")
    assert target.source_type == "video"
    assert target.video_id == "fMHGSx8B9gs"
    assert target.playlist_id is None

    # 2. Shortened youtu.be URL
    target_short = parse_youtube_target("https://youtu.be/fMHGSx8B9gs")
    assert target_short.source_type == "video"
    assert target_short.video_id == "fMHGSx8B9gs"

    # 3. Shorts URL
    target_shorts = parse_youtube_target("https://www.youtube.com/shorts/fMHGSx8B9gs")
    assert target_shorts.source_type == "video"
    assert target_shorts.video_id == "fMHGSx8B9gs"

    # 4. Embed URL
    target_embed = parse_youtube_target("https://www.youtube.com/embed/fMHGSx8B9gs")
    assert target_embed.source_type == "video"
    assert target_embed.video_id == "fMHGSx8B9gs"

    # 5. Raw 11-char video ID
    target_raw = parse_youtube_target("fMHGSx8B9gs")
    assert target_raw.source_type == "video"
    assert target_raw.video_id == "fMHGSx8B9gs"


def test_parse_youtube_target_playlist():
    # Standard playlist URL
    target = parse_youtube_target("https://www.youtube.com/playlist?list=PL_DISTRIBUTED_SYSTEMS_2026")
    assert target.source_type == "playlist"
    assert target.playlist_id == "PL_DISTRIBUTED_SYSTEMS_2026"

    # Mixed URL with both v= and list= defaults to playlist
    mixed = parse_youtube_target("https://www.youtube.com/watch?v=fMHGSx8B9gs&list=PL_DISTRIBUTED_SYSTEMS_2026")
    assert mixed.source_type == "playlist"
    assert mixed.playlist_id == "PL_DISTRIBUTED_SYSTEMS_2026"


@pytest.mark.asyncio
async def test_mock_client_fetch_single_video():
    client = MockYouTubeClient()
    video = await client.fetch_video("fMHGSx8B9gs")
    assert video.video_id == "fMHGSx8B9gs"
    assert "LLM" in video.title or "ChatGPT" in video.title
    assert video.videos[0].duration_seconds > 0



@pytest.mark.asyncio
async def test_playlist_service_preview_single_video(test_db):
    service = PlaylistService(youtube_client=MockYouTubeClient())
    preview = await service.get_preview("https://www.youtube.com/watch?v=fMHGSx8B9gs")

    assert preview.total_videos == 1
    assert preview.source_type == "video"
    assert preview.video_id == "fMHGSx8B9gs"
    assert len(preview.videos) == 1
    assert preview.videos[0].video_id == "fMHGSx8B9gs"



@pytest.mark.asyncio
async def test_pdf_service_single_video_context(tmp_path):
    pdf_service = PDFService()
    
    # Check that jinja environment renders single video cover without fake playlist metadata
    cover_tpl = pdf_service.jinja_env.get_template("cover.html")
    rendered_cover = cover_tpl.render(
        playlist={
            "title": "ChatGPT isn't Magic: The Simplest LLM Explanation Ever",
            "playlist_url": "https://www.youtube.com/watch?v=fMHGSx8B9gs",
            "channel_name": "codestorywithMIK",
            "description": "Standalone technical reference and lecture notes."
        },
        job={"id": "test_job_123"},
        is_single_video=True,
        completed_count=1,
        total_count=1,
        generation_date="October 31, 2026"
    )

    # Asserts that single video badge and creator metadata are rendered
    assert "Technical Reference &amp; Lecture Notes" in rendered_cover or "Technical Reference & Lecture Notes" in rendered_cover
    assert "Standalone Video Masterclass" in rendered_cover
    assert "codestorywithMIK" in rendered_cover
    # Assert that multi-video playlist scope is omitted for single video
    assert "1 of 1 Lectures Synthesized" not in rendered_cover


@pytest.mark.asyncio
async def test_job_service_selected_videos_filtering(test_db):
    from app.services.job_service import JobService
    from app.domain.schemas.job import CreateJobRequest
    from app.core.exceptions import PlaylistScholarException

    job_service = JobService(test_db)

    # 1. Provide a subset of video IDs (unselect others)
    req = CreateJobRequest(
        playlist_input="https://www.youtube.com/playlist?list=PL_DISTRIBUTED_SYSTEMS_2026",
        selected_video_ids=["vid_dist_001", "vid_dist_003"]
    )
    job = await job_service.create_job(req)

    assert job.total_videos == 2
    assert len(job.videos) == 2
    video_ids = [v.video_id for v in job.videos]
    assert video_ids == ["vid_dist_001", "vid_dist_003"]
    assert "vid_dist_002" not in video_ids

    # 2. Assert selecting non-existent videos raises 400 PlaylistScholarException
    invalid_req = CreateJobRequest(
        playlist_input="https://www.youtube.com/playlist?list=PL_DISTRIBUTED_SYSTEMS_2026",
        selected_video_ids=["non_existent_id"]
    )
    with pytest.raises(PlaylistScholarException) as exc_info:
        await job_service.create_job(invalid_req)
    assert exc_info.value.status_code == 400
    assert "No matching videos selected" in exc_info.value.message
