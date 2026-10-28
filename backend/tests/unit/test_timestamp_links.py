import pytest
from app.domain.schemas.transcript import TranscriptData, TranscriptSegment
from app.domain.enums import TranscriptStatus
from app.agents.notes_agent import TechnicalNotesAgent
from app.integrations.openai.mock_client import MockOpenAIClient


@pytest.mark.asyncio
async def test_notes_agent_resolves_timestamps_from_real_segments():
    llm = MockOpenAIClient()
    agent = TechnicalNotesAgent(llm)

    segments = [
        TranscriptSegment(id="seg_0001", start_seconds=12.5, end_seconds=45.0, text="Introduction to consensus."),
        TranscriptSegment(id="seg_0002", start_seconds=46.2, end_seconds=115.8, text="FLP impossibility proof."),
        TranscriptSegment(id="seg_0003", start_seconds=215.0, end_seconds=340.2, text="Leader election and terms.")
    ]
    transcript = TranscriptData(video_id="vid_dist_001", status=TranscriptStatus.AVAILABLE, segments=segments)
    video_meta = {
        "video_id": "vid_dist_001",
        "title": "Consensus",
        "video_url": "https://www.youtube.com/watch?v=vid_dist_001",
        "original_position": 0
    }

    notes = await agent.generate_notes_for_video(video_meta, transcript)
    assert len(notes.sections) > 0

    # Ensure timestamp links match actual segment seconds and not invented numbers
    for section in notes.sections:
        if section.timestamped_watch_url:
            assert "https://www.youtube.com/watch?v=vid_dist_001" in section.timestamped_watch_url
            if section.timestamp_seconds is not None:
                assert section.timestamp_seconds in [12.5, 46.2, 215.0]
                assert f"t={int(section.timestamp_seconds)}s" in section.timestamped_watch_url

