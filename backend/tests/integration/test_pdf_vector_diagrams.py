import os
import pytest
from app.domain.schemas.playlist import GenerationOptions
from app.agents.state import VideoGraphItem
from app.services.pdf_service import PDFService
from app.integrations.openai.mock_client import MockOpenAIClient
from app.integrations.transcripts.mock_provider import MockTranscriptProvider
from app.integrations.storage.local_storage import LocalStorageProvider
from app.integrations.research.mock_research import MockResearchProvider
from app.agents.topic_planner_agent import TopicPlannerAgent
from app.agents.research_agent import ResearchTheoryAgent
from app.agents.notes_agent import TechnicalNotesAgent


@pytest.mark.asyncio
async def test_pdf_compilation_with_enriched_theory_and_diagrams(tmp_path):
    storage = LocalStorageProvider(base_dir=str(tmp_path))
    pdf_service = PDFService(storage=storage)
    llm = MockOpenAIClient()
    transcript_prov = MockTranscriptProvider()
    research_prov = MockResearchProvider()

    planner = TopicPlannerAgent(llm)
    research_agent = ResearchTheoryAgent(research_prov)
    notes_agent = TechnicalNotesAgent(llm)

    meta = {
        "video_id": "vid_dist_001",
        "title": "Distributed Consensus & Raft",
        "channel_title": "MIT Distributed Systems Lab",
        "duration_seconds": 1245,
        "video_url": "https://www.youtube.com/watch?v=vid_dist_001",
        "original_position": 0
    }

    t1 = await transcript_prov.get_transcript("vid_dist_001")
    plan = await planner.plan_topics_for_video(meta, t1)
    bundle = await research_agent.research_for_video(meta, plan, enable_research=True)

    notes = await notes_agent.generate_notes_for_video(
        video_metadata=meta,
        transcript=t1,
        detail_level="comprehensive",
        topic_plan=plan,
        research_bundle=bundle
    )
    visual = await llm.generate_visual_spec(notes)

    assert visual is not None
    assert visual.mermaid_code is not None

    videos = [
        VideoGraphItem(
            video_id="vid_dist_001",
            original_position=0,
            title="Distributed Consensus & Raft",
            video_url="https://www.youtube.com/watch?v=vid_dist_001",
            duration_seconds=1245,
            channel_title="MIT Distributed Systems Lab",
            notes=notes,
            visual=visual
        )
    ]

    artifact = await pdf_service.compile_playlist_pdf(
        job_id="test_vector_diagram_job",
        playlist_title="Advanced Systems Architecture",
        playlist_url="https://www.youtube.com/playlist?list=PL_TEST_VECTOR",
        channel_name="MIT Systems Lab",
        videos=videos,
        options=GenerationOptions(enable_visuals=True)
    )

    assert artifact.file_size_bytes > 5000
    assert os.path.exists(artifact.file_path)

    # Verify PDF contains valid PDF signature
    with open(artifact.file_path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-"

