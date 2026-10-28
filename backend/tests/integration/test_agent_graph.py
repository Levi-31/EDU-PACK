import pytest
from app.domain.schemas.playlist import GenerationOptions
from app.agents.state import PlaylistGraphState, VideoGraphItem
from app.agents.graph import PlaylistWorkflowOrchestrator
from app.integrations.transcripts.mock_provider import MockTranscriptProvider
from app.integrations.openai.mock_client import MockOpenAIClient
from app.domain.enums import VideoProcessingStatus


@pytest.mark.asyncio
async def test_agent_graph_workflow_preserves_order_and_handles_failures():
    transcript_provider = MockTranscriptProvider()
    llm_client = MockOpenAIClient()

    orchestrator = PlaylistWorkflowOrchestrator(
        transcript_provider=transcript_provider,
        llm_client=llm_client,
        pdf_service=None
    )

    # 4 Videos: video 3 is unavailable
    videos = [
        VideoGraphItem(
            video_id="vid_dist_001",
            original_position=0,
            title="Consensus",
            video_url="https://youtube.com/watch?v=vid_dist_001",
            is_available=True
        ),
        VideoGraphItem(
            video_id="vid_dist_002",
            original_position=1,
            title="Event Sourcing",
            video_url="https://youtube.com/watch?v=vid_dist_002",
            is_available=True
        ),
        VideoGraphItem(
            video_id="vid_dist_003",
            original_position=2,
            title="Private Video",
            video_url="https://youtube.com/watch?v=vid_dist_003",
            is_available=True  # provider will report transcript unavailable
        ),
        VideoGraphItem(
            video_id="vid_dist_004",
            original_position=3,
            title="Kafka Storage",
            video_url="https://youtube.com/watch?v=vid_dist_004",
            is_available=True
        )
    ]

    initial_state = PlaylistGraphState(
        job_id="test_job_001",
        playlist_id="PL_TEST",
        playlist_title="Distributed Systems",
        playlist_url="https://youtube.com/playlist?list=PL_TEST",
        options=GenerationOptions(),
        videos=videos
    )

    final_state = await orchestrator.run(initial_state)

    # 1. Total count preserved
    assert len(final_state.videos) == 4

    # 2. Strict ordering preserved: 0, 1, 2, 3
    assert [v.original_position for v in final_state.videos] == [0, 1, 2, 3]

    # 3. vid_dist_001 succeeded with notes and visual
    assert final_state.videos[0].status == VideoProcessingStatus.COMPLETED
    assert final_state.videos[0].notes is not None
    assert final_state.videos[0].visual is not None

    # 4. vid_dist_003 failed transcript gracefully and DID NOT fabricate notes!
    assert final_state.videos[2].status == VideoProcessingStatus.TRANSCRIPT_FAILED
    assert final_state.videos[2].notes is None
    assert "private" in (final_state.videos[2].failure_reason or "").lower()

    # 5. vid_dist_004 succeeded despite previous video failure
    assert final_state.videos[3].status == VideoProcessingStatus.COMPLETED
    assert final_state.videos[3].notes is not None
