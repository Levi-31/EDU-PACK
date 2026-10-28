import os
import pytest
from app.domain.schemas.playlist import GenerationOptions
from app.agents.state import VideoGraphItem
from app.services.pdf_service import PDFService
from app.integrations.openai.mock_client import MockOpenAIClient
from app.integrations.transcripts.mock_provider import MockTranscriptProvider
from app.integrations.storage.local_storage import LocalStorageProvider


@pytest.mark.asyncio
async def test_pdf_compilation_and_artifact_validation(tmp_path):
    storage = LocalStorageProvider(base_dir=str(tmp_path))
    pdf_service = PDFService(storage=storage)
    llm = MockOpenAIClient()
    transcript_prov = MockTranscriptProvider()

    # Generate real sample notes for 2 videos
    t1 = await transcript_prov.get_transcript("vid_dist_001")
    notes1 = await llm.generate_structured_notes(
        {"video_id": "vid_dist_001", "title": "Consensus", "original_position": 0},
        t1.get_text(),
        [s.model_dump() for s in t1.segments]
    )
    visual1 = await llm.generate_visual_spec(notes1)

    videos = [
        VideoGraphItem(
            video_id="vid_dist_001",
            original_position=0,
            title="Consensus",
            video_url="https://youtube.com/watch?v=vid_dist_001",
            notes=notes1,
            visual=visual1
        ),
        VideoGraphItem(
            video_id="vid_dist_003",
            original_position=1,
            title="Unavailable Lecture",
            video_url="https://youtube.com/watch?v=vid_dist_003",
            is_available=False,
            failure_reason="Video is private"
        )
    ]

    artifact = await pdf_service.compile_playlist_pdf(
        job_id="test_pdf_job",
        playlist_title="Distributed Systems",
        playlist_url="https://youtube.com/playlist?list=PL_TEST",
        channel_name="MIT Lab",
        videos=videos,
        options=GenerationOptions()
    )

    assert artifact.file_size_bytes > 0
    assert os.path.exists(artifact.file_path)
    assert artifact.checksum_sha256 != ""
    assert artifact.download_url == "/api/v1/jobs/test_pdf_job/download"

