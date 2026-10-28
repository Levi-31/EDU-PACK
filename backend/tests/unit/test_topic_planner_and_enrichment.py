import pytest
from app.domain.enums import VisualType
from app.domain.schemas.transcript import TranscriptData, TranscriptSegment
from app.domain.schemas.topic_plan import VideoTopicPlan
from app.domain.schemas.notes import ReviewReport
from app.integrations.openai.mock_client import MockOpenAIClient
from app.integrations.research.mock_research import MockResearchProvider
from app.agents.topic_planner_agent import TopicPlannerAgent
from app.agents.research_agent import ResearchTheoryAgent
from app.agents.notes_agent import TechnicalNotesAgent
from app.agents.visual_agent import VisualDiagramAgent
from app.agents.review_agent import NotesReviewAgent


@pytest.fixture
def sample_transcript():
    return TranscriptData(
        video_id="vid_dist_001",
        language="en",
        source="youtube",
        segments=[
            TranscriptSegment(
                id="seg_0001",
                start_seconds=12.5,
                end_seconds=22.5,
                text="In this lecture, we examine distributed consensus and replicated state machines."
            ),
            TranscriptSegment(
                id="seg_0002",
                start_seconds=215.0,
                end_seconds=230.0,
                text="Raft servers transition between Follower, Candidate, and Leader states."
            ),
            TranscriptSegment(
                id="seg_0003",
                start_seconds=342.0,
                end_seconds=354.0,
                text="Log entries require acknowledgment from a majority quorum to be committed."
            )
        ]
    )


@pytest.mark.asyncio
async def test_topic_planner_agent(sample_transcript):
    client = MockOpenAIClient()
    agent = TopicPlannerAgent(client)
    meta = {"video_id": "vid_dist_001", "title": "Distributed Consensus & Raft"}

    plan = await agent.plan_topics_for_video(meta, sample_transcript)
    assert isinstance(plan, VideoTopicPlan)
    assert len(plan.planned_topics) >= 2
    assert plan.planned_topics[0].learning_objectives
    assert plan.planned_topics[0].research_queries


@pytest.mark.asyncio
async def test_research_theory_agent(sample_transcript):
    client = MockOpenAIClient()
    planner = TopicPlannerAgent(client)
    meta = {"video_id": "vid_dist_001", "title": "Distributed Consensus & Raft"}
    plan = await planner.plan_topics_for_video(meta, sample_transcript)

    research_agent = ResearchTheoryAgent(MockResearchProvider(), max_queries_per_video=3)
    bundle = await research_agent.research_for_video(meta, plan, enable_research=True)

    assert bundle.video_id == "vid_dist_001"
    assert len(bundle.sources) > 0
    assert bundle.sources[0].url.startswith("http")


@pytest.mark.asyncio
async def test_technical_notes_agent_demarcation_and_timestamps(sample_transcript):
    client = MockOpenAIClient()
    planner = TopicPlannerAgent(client)
    research_agent = ResearchTheoryAgent(MockResearchProvider())
    notes_agent = TechnicalNotesAgent(client)

    meta = {
        "video_id": "vid_dist_001",
        "title": "Distributed Consensus & Raft",
        "channel_title": "MIT Lab",
        "duration_seconds": 1200,
        "video_url": "https://www.youtube.com/watch?v=vid_dist_001",
        "original_position": 0
    }
    plan = await planner.plan_topics_for_video(meta, sample_transcript)
    bundle = await research_agent.research_for_video(meta, plan, enable_research=True)

    notes = await notes_agent.generate_notes_for_video(
        video_metadata=meta,
        transcript=sample_transcript,
        detail_level="comprehensive",
        topic_plan=plan,
        research_bundle=bundle
    )

    # Verify structured fields
    assert notes.comprehensive_theory_background is not None
    assert len(notes.sections) >= 2
    
    # Verify strict demarcation
    s1 = notes.sections[0]
    assert s1.from_video is not None
    assert s1.additional_theory is not None
    assert s1.comparison_table_markdown is not None
    assert s1.cited_sources

    # Verify application-grounded timestamp links
    assert s1.timestamp_seconds == 12.5
    assert "t=12s" in s1.timestamped_watch_url


@pytest.mark.asyncio
async def test_visual_diagram_agent_validation():
    client = MockOpenAIClient()
    visual_agent = VisualDiagramAgent(client)
    
    # Valid Mermaid prefix checks
    assert visual_agent._is_valid_mermaid("graph TD\n  A --> B")
    assert visual_agent._is_valid_mermaid("sequenceDiagram\n  Alice->>Bob: Hello")
    assert visual_agent._is_valid_mermaid("flowchart LR\n  Start --> End")
    assert visual_agent._is_valid_mermaid("stateDiagram-v2\n  [*] --> Still")
    assert not visual_agent._is_valid_mermaid("alert('hacked')")
    assert not visual_agent._is_valid_mermaid("SELECT * FROM users")


@pytest.mark.asyncio
async def test_notes_review_agent_bounded_revision(sample_transcript):
    client = MockOpenAIClient()
    review_agent = NotesReviewAgent(client, max_revisions=1)
    notes_agent = TechnicalNotesAgent(client)

    meta = {"video_id": "vid_dist_001", "title": "Distributed Consensus"}
    notes = await notes_agent.generate_notes_for_video(meta, sample_transcript)

    # Approved review should not require revision
    report, needs_revision = await review_agent.review(notes, sample_transcript, current_revision_count=0)
    assert report.status == "APPROVED"
    assert not needs_revision
