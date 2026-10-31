import pytest
from app.agents.notes_agent import TechnicalNotesAgent
from app.agents.visual_agent import VisualDiagramAgent
from app.domain.schemas.notes import (
    StructuredVideoNotes,
    NoteTopicSection,
    GlossaryItem,
    Flashcard,
    ReviewReport,
)
from app.services.pdf_service import _normalize_glossary, _deduplicate_flashcards
from app.integrations.openai.mock_client import MockOpenAIClient


def test_placeholder_scrubbing():
    dirty_text = (
        "The microservices architecture decomposes applications into smaller services. "
        "A diagram could be used here to depict interactions between these services and the databases. "
        "Each service is independently scalable."
    )
    cleaned = TechnicalNotesAgent._scrub_text(dirty_text)
    assert "diagram could be used" not in cleaned.lower()
    assert "The microservices architecture decomposes applications into smaller services." in cleaned
    assert "Each service is independently scalable." in cleaned

    insert_image_text = "Here is the flow. Insert image of network architecture. Then packet routing occurs."
    cleaned2 = TechnicalNotesAgent._scrub_text(insert_image_text)
    assert "insert image" not in cleaned2.lower()
    assert "Then packet routing occurs." in cleaned2


def test_glossary_normalization_and_deduplication():
    raw_items = [
        GlossaryItem(term="IAM", definition="Identity and Access Management service in GCP."),
        GlossaryItem(term="Identity and Access Management (IAM)", definition="A comprehensive framework of policies and technologies ensuring that the right users have appropriate access to technology resources."),
        GlossaryItem(term="GCP", definition="Google Cloud Platform."),
        GlossaryItem(term="Google Cloud Platform (GCP)", definition="A suite of cloud computing services offered by Google running on the same infrastructure that Google uses internally."),
        GlossaryItem(term="API", definition="Application Programming Interface."),
        GlossaryItem(term="VPC", definition="Virtual Private Cloud network."),
        GlossaryItem(term="Virtual Private Cloud (VPC)", definition="A configurable pool of shared resources allocated within a public cloud environment."),
        GlossaryItem(term="Dockerfile", definition="A text document containing commands to assemble a Docker image."),
        GlossaryItem(term="dockerfile", definition="Text file to build container."),
    ]

    deduped = _normalize_glossary(raw_items)
    terms = [item.term for item in deduped]

    # Check that duplicates were merged into canonical expansions
    assert "Identity and Access Management (IAM)" in terms
    assert "IAM" not in [t for t in terms if t != "Identity and Access Management (IAM)"]
    assert "Google Cloud Platform (GCP)" in terms
    assert "Virtual Private Cloud (VPC)" in terms

    # Check that the more comprehensive definition is retained
    iam_item = next(item for item in deduped if "IAM" in item.term)
    assert "comprehensive framework of policies" in iam_item.definition

    # Verify alphabetical sorting
    assert terms == sorted(terms, key=lambda x: x.lower())


def test_flashcard_deduplication():
    cards = [
        Flashcard(question="What is GCP IAM?", answer="Controls who can do what on which resources."),
        Flashcard(question="What is GCP IAM?", answer="Duplicate answer."),
        Flashcard(question="What is a VPC?", answer="Virtual Private Cloud."),
    ]
    deduped = _deduplicate_flashcards(cards)
    assert len(deduped) == 2
    assert deduped[0].question == "What is GCP IAM?"
    assert deduped[1].question == "What is a VPC?"


def test_visual_agent_mermaid_cleaning_and_fences():
    fenced_dsl = """```mermaid
flowchart TD
    A["Client"] --> B["Cloud Load Balancer"]
    B --> C["Backend VM"]
```"""
    cleaned = VisualDiagramAgent._clean_mermaid_dsl(fenced_dsl)
    assert not cleaned.startswith("```")
    assert not cleaned.endswith("```")
    assert cleaned.startswith("flowchart TD")

    agent = VisualDiagramAgent(MockOpenAIClient())
    assert agent._is_valid_mermaid(fenced_dsl) is True

    # Test single-dash arrow repair
    broken_arrow_dsl = """flowchart TD;
    A(Initialize LangGraph) --> B{Input Valid?};
    H --> I(Memory Update) -> A;"""
    cleaned_arrows = VisualDiagramAgent._clean_mermaid_dsl(broken_arrow_dsl)
    assert "--> A" in cleaned_arrows
    assert " -> A" not in cleaned_arrows
    assert not cleaned_arrows.endswith(";")

    # Test joined statements splitting
    joined_dsl = """flowchart TD A["Input Data"] --> B["Agentic AI Model"] B --> C["Decision Making"]"""
    cleaned_joined = VisualDiagramAgent._clean_mermaid_dsl(joined_dsl)
    assert "flowchart TD\n" in cleaned_joined
    assert "\n    B -->" in cleaned_joined


def test_review_report_dimensional_scoring_defaults():
    report = ReviewReport()
    assert report.status == "APPROVED"
    assert report.transcript_coverage >= 1.0
    assert report.explanation_depth >= 1.0
    assert report.technical_accuracy >= 1.0
    assert report.command_correctness >= 1.0
    assert report.has_critical_failure is False


def test_pdf_templates_omit_duration_and_channel():
    import jinja2
    from pathlib import Path
    
    templates_dir = Path(__file__).resolve().parents[2] / "app" / "templates" / "pdf"
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(templates_dir)))
    
    # 1. Verify TOC template has no duration and no channel references
    toc_tpl = env.get_template("toc.html")
    sample_chapters = [
        {
            "position": 0,
            "title": "Agentic AI using LangGraph",
            "channel_title": "CampusX",
            "duration_formatted": "16:58",
            "is_available": True,
            "has_notes": True
        },
        {
            "position": 1,
            "title": "Generative AI vs Agentic AI",
            "channel_title": "CampusX",
            "duration_formatted": "62:44",
            "is_available": False,
            "has_notes": False
        }
    ]
    rendered_toc = toc_tpl.render(chapters=sample_chapters)
    assert "CampusX" not in rendered_toc
    assert "16:58" not in rendered_toc
    assert "62:44" not in rendered_toc
    assert "Agentic AI using LangGraph" in rendered_toc
    assert "Transcript Unavailable" in rendered_toc
    assert "toc-entry" in rendered_toc

    # 2. Verify chapter template has no duration chip and no channel chip
    chapter_tpl = env.get_template("chapter.html")
    rendered_chapter = chapter_tpl.render(
        item={**sample_chapters[0], "has_notes": False},
        loop_index=1
    )
    assert "CampusX" not in rendered_chapter
    assert "16:58" not in rendered_chapter
    assert "Watch on YouTube" in rendered_chapter

    # 3. Verify cover template has no channel name
    cover_tpl = env.get_template("cover.html")
    rendered_cover = cover_tpl.render(
        playlist={"title": "LangGraph Course", "playlist_url": "https://youtube.com/playlist?list=xyz", "channel_name": "CampusX"},
        completed_count=2,
        total_count=2,
        generation_date="October 29, 2026",
        job={"id": "test-job-1234567890"}
    )
    assert "CampusX" not in rendered_cover
    assert "Document ID" not in rendered_cover
    assert "Curriculum Scope" in rendered_cover

    # 4. Verify styles.css contains break-inside: avoid for toc-entry
    styles_file = templates_dir / "styles.css"
    css_content = styles_file.read_text()
    assert ".toc-entry" in css_content
    assert "break-inside: avoid" in css_content


def test_clean_technical_title():
    from app.services.pdf_service import clean_technical_title

    assert clean_technical_title("Model Context Protocol | Mini Playlist | MCP Trilogy | CampusX") == "Model Context Protocol — Introduction"
    assert clean_technical_title("Model Context Protocol - The Why | MCP Trilogy | CampusX") == "Why Model Context Protocol?"
    assert clean_technical_title("MCP Architecture | Model Context Protocol Architecture | CampusX") == "MCP Architecture"
    assert clean_technical_title("How to Build Local MCP Servers | MCP Trilogy | CampusX") == "Building Local MCP Servers"
    assert clean_technical_title("How to Build & Deploy Remote MCP Servers | MCP Trilogy | CampusX") == "Deploying Remote MCP Servers"
    assert clean_technical_title("How to build MCP Clients | MCP Trilogy | CampusX") == "Building MCP Clients"


def test_terminology_and_dummy_domain_scrubbing():
    from app.agents.notes_agent import TechnicalNotesAgent
    from app.domain.schemas.notes import StructuredVideoNotes, NoteTopicSection
    from app.domain.schemas.research import ResearchSource

    # 1. Terminology correction
    dirty_text = "Building local MCP (Model Command Protocol) servers from scratch."
    cleaned = TechnicalNotesAgent._scrub_text(dirty_text)
    assert "Model Context Protocol" in cleaned
    assert "Model Command Protocol" not in cleaned

    # 2. Dummy domain filtering in citations
    notes = StructuredVideoNotes(
        video_id="vid_test",
        video_title="MCP Architecture",
        video_url="https://youtube.com/watch?v=vid_test",
        executive_summary="Summary",
        revision_sheet="Key takeaways and recap.",
        sections=[
            NoteTopicSection(
                title="Overview",
                markdown_content="Overview of MCP",
                from_video="Content",
                cited_sources=[
                    ResearchSource(title="Doc 1", url="https://example.com/spec", domain="example.com", snippet=""),
                    ResearchSource(title="Official MCP Spec", url="https://spec.modelcontextprotocol.io", domain="modelcontextprotocol.io", snippet="")
                ]
            )
        ],
        all_sources=[
            ResearchSource(title="Cloud Doc", url="https://cloud.domain.com/docs", domain="domain.com", snippet=""),
            ResearchSource(title="Official MCP Spec", url="https://spec.modelcontextprotocol.io", domain="modelcontextprotocol.io", snippet="")
        ]
    )

    agent = TechnicalNotesAgent(MockOpenAIClient())
    agent._clean_notes_placeholders(notes)

    assert len(notes.all_sources) == 1
    assert notes.all_sources[0].url == "https://spec.modelcontextprotocol.io"
    assert len(notes.sections[0].cited_sources) == 1
    assert notes.sections[0].cited_sources[0].url == "https://spec.modelcontextprotocol.io"


def test_multilingual_transcript_rendering():
    import jinja2
    from pathlib import Path
    
    templates_dir = Path(__file__).resolve().parents[2] / "app" / "templates" / "pdf"
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(templates_dir)))
    env.filters["markdown"] = lambda x: x or ""

    chapter_tpl = env.get_template("chapter.html")
    hindi_text = "MCP आर्किटेक्चर: होस्ट और सर्वर। जब यूजर एक प्रॉम्प्ट भेजता है तो होस्ट सर्वर को रिक्वेस्ट भेजता है।"
    
    rendered = chapter_tpl.render(
        item={
            "position": 0,
            "title": "MCP Architecture",
            "video_url": "https://youtube.com/watch?v=test",
            "has_notes": True,
            "is_available": True,
            "notes": {
                "executive_summary": "Executive summary with Hindi context",
                "comprehensive_theory_background": "Theory background",
                "sections": [
                    {
                        "title": "Architecture Overview",
                        "from_video": hindi_text,
                        "additional_theory": "Supplementary details explaining host and server decoupling.",
                        "code_snippets": [],
                        "callouts": [],
                        "cited_sources": []
                    }
                ]
            }
        },
        loop_index=1
    )

    assert "आर्किटेक्चर" in rendered
    assert "होस्ट और सर्वर" in rendered
    assert "From the Video" in rendered
    assert "Supplementary Explanation" in rendered


def test_salutations_scrubbed_from_video_and_notes():
    from app.agents.notes_agent import TechnicalNotesAgent

    # Hindi conversational salutation
    hindi_salutation = "हाय गाइस, माय नेम इज नितेश एंड यू वेलकम टू माय YouTube चैनल। इस वीडियो में भी हम लोग अपना एजेंटिक एआई यूजिंग लैंग्राफ प्लेलिस्ट कंटिन्यू करेंगे... आज हम मेमोरी के बारे में सीखेंगे।"
    scrubbed_hindi = TechnicalNotesAgent._scrub_salutations(hindi_salutation)
    assert "हाय गाइस" not in scrubbed_hindi
    assert "माय नेम इज नितेश" not in scrubbed_hindi
    assert "YouTube चैनल" not in scrubbed_hindi
    assert "प्लेलिस्ट कंटिन्यू" not in scrubbed_hindi
    assert "आज हम मेमोरी के बारे में सीखेंगे" in scrubbed_hindi

    # Pure salutation becomes empty
    pure_salutation = "हाय गाइस, माय नेम इज नितेश एंड यू वेलकम टू माय YouTube चैनल। इस वीडियो में भी हम लोग अपना एजेंटिक एआई यूजिंग लैंग्राफ प्लेलिस्ट कंटिन्यू करेंगे..."
    assert len(TechnicalNotesAgent._scrub_salutations(pure_salutation)) == 0

    # English YouTube intro and salutation
    english_intro = "Hey guys, welcome back to my YouTube channel! My name is Alex and don't forget to like and subscribe. Today we explore Raft log compaction."
    scrubbed_en = TechnicalNotesAgent._scrub_salutations(english_intro)
    assert "welcome back to my YouTube channel" not in scrubbed_en.lower()
    assert "like and subscribe" not in scrubbed_en.lower()
    assert "Today we explore Raft log compaction" in scrubbed_en


def test_mermaid_deep_validation_rejects_truncated_syntax():
    from app.agents.visual_agent import VisualDiagramAgent
    from app.integrations.openai.mock_client import MockOpenAIClient

    agent = VisualDiagramAgent(MockOpenAIClient())

    # Truncated diagram from user bug (A[ with unclosed subgraph and unclosed bracket)
    broken_dsl = "flowchart TD\n    subgraph LTM_Architecture\n        direction TB\n        A["
    assert agent._is_valid_mermaid(broken_dsl) is False

    # Missing subgraph end
    missing_end_dsl = """flowchart TD
    subgraph Architecture
        A["Client"] --> B["Server"]
"""
    assert agent._is_valid_mermaid(missing_end_dsl) is False

    # Valid, balanced complete diagram
    valid_dsl = """flowchart TD
    subgraph Architecture
        A["Client"] --> B["Server"]
    end
"""
    assert agent._is_valid_mermaid(valid_dsl) is True




