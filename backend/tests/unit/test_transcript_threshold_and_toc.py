import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from app.agents.graph import PlaylistWorkflowOrchestrator
from app.agents.state import PlaylistGraphState, VideoGraphItem
from app.domain.enums import VideoProcessingStatus, JobStatus, NoteDetailLevel, PDFTheme
from app.domain.schemas.playlist import GenerationOptions
from app.domain.schemas.notes import StructuredVideoNotes, NoteTopicSection
from app.core.exceptions import PDFGenerationException
from app.services.pdf_service import PDFService
from app.integrations.pdf.reportlab_renderer import ReportLabFallbackRenderer


def create_sample_notes(vid: str, title: str) -> StructuredVideoNotes:
    return StructuredVideoNotes(
        video_id=vid,
        video_title=title,
        video_url=f"https://youtube.com/watch?v={vid}",
        executive_summary=f"Executive summary for {title}",
        comprehensive_theory_background=f"Foundational architectural context and deep theory for {title}.",
        revision_sheet="Key takeaways and recap for this topic.",
        sections=[
            NoteTopicSection(
                title="Core Principles",
                markdown_content="Detailed technical concepts and principles.",
                from_video="Video lecture transcription content.",
                additional_theory="Supplementary architectural background."
            )
        ]
    )


@pytest.mark.asyncio
async def test_single_video_unavailable_aborts_pdf():
    """If a single video has no transcript/notes, abort PDF generation with explanatory message."""
    mock_pdf_service = MagicMock()
    mock_pdf_service.compile_playlist_pdf = AsyncMock()

    orchestrator = PlaylistWorkflowOrchestrator(
        transcript_provider=MagicMock(),
        llm_client=MagicMock(),
        pdf_service=mock_pdf_service
    )

    state = PlaylistGraphState(
        job_id="job-single-unavail",
        playlist_id="unavail123",
        playlist_title="Single Video Without Captions",
        playlist_url="https://youtube.com/watch?v=unavail123",
        options=GenerationOptions(
            detail_level=NoteDetailLevel.STANDARD,
            transcript_language="en",
            enable_visuals=False,
            pdf_theme=PDFTheme.EDITORIAL_NAVY,
            max_revisions=1
        ),
        videos=[
            VideoGraphItem(
                video_id="unavail123",
                original_position=0,
                title="Single Video Without Captions",
                video_url="https://youtube.com/watch?v=unavail123",
                is_available=False,
                status=VideoProcessingStatus.TRANSCRIPT_FAILED,
                notes=None
            )
        ]
    )

    result = await orchestrator._compile_pdf_node(state)
    assert result["current_stage"] == "PDF_ABORTED"
    assert "Transcript is unavailable for this video" in result["error_summary"]
    # PDF service must NOT be called
    mock_pdf_service.compile_playlist_pdf.assert_not_called()


@pytest.mark.asyncio
async def test_playlist_below_fifty_percent_threshold_aborts_pdf():
    """If <50% of videos in a playlist have transcripts, abort PDF generation with explanatory message."""
    mock_pdf_service = MagicMock()
    mock_pdf_service.compile_playlist_pdf = AsyncMock()

    orchestrator = PlaylistWorkflowOrchestrator(
        transcript_provider=MagicMock(),
        llm_client=MagicMock(),
        pdf_service=mock_pdf_service
    )

    # 4 videos: only 1 completed (25% available, < 50%)
    videos = [
        VideoGraphItem(
            video_id="v1",
            original_position=0,
            title="Video 1",
            video_url="https://youtube.com/watch?v=v1",
            notes=create_sample_notes("v1", "Video 1"),
            status=VideoProcessingStatus.COMPLETED
        ),
        VideoGraphItem(
            video_id="v2",
            original_position=1,
            title="Video 2",
            video_url="https://youtube.com/watch?v=v2",
            notes=None,
            status=VideoProcessingStatus.TRANSCRIPT_FAILED
        ),
        VideoGraphItem(
            video_id="v3",
            original_position=2,
            title="Video 3",
            video_url="https://youtube.com/watch?v=v3",
            notes=None,
            status=VideoProcessingStatus.TRANSCRIPT_FAILED
        ),
        VideoGraphItem(
            video_id="v4",
            original_position=3,
            title="Video 4",
            video_url="https://youtube.com/watch?v=v4",
            notes=None,
            status=VideoProcessingStatus.TRANSCRIPT_FAILED
        ),
    ]

    state = PlaylistGraphState(
        job_id="job-playlist-low-avail",
        playlist_id="PL123",
        playlist_title="Course with Mostly Missing Captions",
        playlist_url="https://youtube.com/playlist?list=PL123",
        options=GenerationOptions(
            detail_level=NoteDetailLevel.STANDARD,
            transcript_language="en",
            enable_visuals=False,
            pdf_theme=PDFTheme.EDITORIAL_NAVY,
            max_revisions=1
        ),
        videos=videos
    )

    result = await orchestrator._compile_pdf_node(state)
    assert result["current_stage"] == "PDF_ABORTED"
    assert "majority of videos in this playlist" in result["error_summary"]
    assert "3/4 unavailable" in result["error_summary"]
    assert "25% available" in result["error_summary"]
    mock_pdf_service.compile_playlist_pdf.assert_not_called()


@pytest.mark.asyncio
async def test_playlist_above_threshold_renders_pdf_and_omits_unavailable_pages():
    """
    If >= 50% of videos have transcripts:
    - PDF is compiled.
    - TOC includes unavailable videos with 'Transcript Unavailable' and YouTube link.
    - Document body does NOT render unavailable video pages.
    """
    pdf_service = PDFService(renderer=ReportLabFallbackRenderer())

    # 4 videos: 3 available, 1 unavailable (75% available >= 50%)
    videos = [
        VideoGraphItem(
            video_id="v1",
            original_position=0,
            title="Introduction to LangChain",
            video_url="https://youtube.com/watch?v=v1",
            notes=create_sample_notes("v1", "Introduction to LangChain"),
            status=VideoProcessingStatus.COMPLETED
        ),
        VideoGraphItem(
            video_id="v2",
            original_position=1,
            title="Prompt Templates Deep Dive",
            video_url="https://youtube.com/watch?v=v2",
            is_available=False,
            notes=None,
            status=VideoProcessingStatus.TRANSCRIPT_FAILED,
            failure_reason="Subtitles were disabled by uploader."
        ),
        VideoGraphItem(
            video_id="v3",
            original_position=2,
            title="Output Parsers and Chains",
            video_url="https://youtube.com/watch?v=v3",
            notes=create_sample_notes("v3", "Output Parsers and Chains"),
            status=VideoProcessingStatus.COMPLETED
        ),
        VideoGraphItem(
            video_id="v4",
            original_position=3,
            title="Retrievers and Vector Stores",
            video_url="https://youtube.com/watch?v=v4",
            notes=create_sample_notes("v4", "Retrievers and Vector Stores"),
            status=VideoProcessingStatus.COMPLETED
        ),
    ]

    options = GenerationOptions(
        detail_level=NoteDetailLevel.STANDARD,
        transcript_language="en",
        enable_visuals=False,
        pdf_theme=PDFTheme.EDITORIAL_NAVY,
        max_revisions=1
    )

    # Test PDFService defensive check directly
    # Compile document HTML using the internal template rendering
    sorted_videos = sorted(videos, key=lambda v: v.original_position)
    chapters_data = []
    for idx, v in enumerate(sorted_videos, 1):
        has_notes = v.notes is not None
        chapters_data.append({
            "position": v.original_position,
            "chapter_idx": idx,
            "title": v.title,
            "clean_title": v.title,
            "channel_title": "CampusX",
            "duration_formatted": "15:00",
            "video_url": v.video_url,
            "thumbnail_url": "",
            "is_available": v.is_available,
            "has_notes": has_notes,
            "failure_reason": v.failure_reason,
            "notes": v.notes,
            "visual": None,
            "is_mock": False,
            "page_number": f"{idx:02d}" if has_notes else "--"
        })

    tpl = pdf_service.jinja_env.get_template("base.html")
    rendered_html = tpl.render(
        playlist={
            "title": "LangChain Full Course",
            "playlist_url": "https://youtube.com/playlist?list=PL123",
            "channel_name": "CampusX",
            "description": "Comprehensive course"
        },
        job={"id": "job-test-toc"},
        chapters=chapters_data,
        review_page_number="12",
        completed_count=3,
        total_count=4,
        is_single_video=False,
        generation_date="November 02, 2026",
        consolidated_flashcards=[],
        consolidated_glossary=[],
        css_styles="",
        mermaid_js=""
    )

    # 1. Verify TOC entries
    # Video 1: Available -> Has anchor #chapter-1
    assert 'href="#chapter-1"' in rendered_html
    # Video 2: Unavailable -> Must NOT have anchor #chapter-2
    assert 'href="#chapter-2"' not in rendered_html
    # Video 2: Must show Transcript Unavailable badge and direct YouTube link in TOC
    assert 'toc-badge-unavailable' in rendered_html
    assert 'Transcript Unavailable' in rendered_html
    assert 'href="https://youtube.com/watch?v=v2"' in rendered_html
    assert 'Watch on YouTube' in rendered_html

    # 2. Verify Body Chapters:
    # Chapter 1 (v1) and Chapter 3 (v3) must have chapter-container
    assert 'id="chapter-1"' in rendered_html
    assert 'id="chapter-3"' in rendered_html
    assert 'id="chapter-4"' in rendered_html
    # Chapter 2 (v2) must NOT have a chapter-container or page rendered in body
    assert 'id="chapter-2"' not in rendered_html
    # Ensure no unavailable-box placeholder is in the rendered HTML
    assert 'unavailable-box' not in rendered_html
    assert 'Transcript / Video Inaccessible' not in rendered_html
