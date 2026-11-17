import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from jinja2 import Environment, FileSystemLoader

from app.integrations.pdf.renderer import strip_pdf_metadata
from app.integrations.pdf.reportlab_renderer import ReportLabFallbackRenderer
from app.modules.research.research_service import ResearchService

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "app" / "templates" / "pdf"

CHROMIUM_STYLE_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<</Title <FEFF0041>\n/Creator (Chromium)\n/Producer (Skia/PDF m156)\n"
    b"/CreationDate (D:20261102192336+00'00')\n/ModDate (D:20261102192336+00'00')>>\nendobj\n"
    b"2 0 obj\n<</Producer (not the info object)>>\nendobj\n"
    b"trailer\n<</Size 3\n/Info 1 0 R>>\n"
)


def test_strip_pdf_metadata_blanks_info_dict_but_keeps_title_and_offsets():
    stripped = strip_pdf_metadata(CHROMIUM_STYLE_PDF)

    assert len(stripped) == len(CHROMIUM_STYLE_PDF)
    assert b"/Title <FEFF0041>" in stripped
    for removed in (b"Chromium", b"Skia", b"/CreationDate", b"/ModDate"):
        assert removed not in stripped
    # Only the info object is touched
    assert b"/Producer (not the info object)" in stripped
    assert stripped.index(b"2 0 obj") == CHROMIUM_STYLE_PDF.index(b"2 0 obj")


def test_strip_pdf_metadata_leaves_pdf_without_info_dict_unchanged():
    pdf = b"%PDF-1.4\ntrailer\n<</Size 1>>\n"
    assert strip_pdf_metadata(pdf) == pdf


def test_reportlab_fallback_output_has_no_renderer_metadata():
    pdf = asyncio.run(ReportLabFallbackRenderer().render_html_to_pdf("<html></html>"))

    assert pdf.startswith(b"%PDF")
    assert b"(tokens.to.systems)" in pdf
    for removed in (b"www.reportlab.com", b"/Producer", b"/Creator", b"/CreationDate", b"anonymous"):
        assert removed not in pdf


def test_watermark_is_included_in_both_documents_and_not_selectable_text():
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    watermark = env.get_template("watermark.html").render()

    assert "position: fixed" in watermark
    assert "<path" in watermark
    assert "tokens.to.systems" not in watermark
    for document in ("base.html", "research.html"):
        assert '{% include "watermark.html" %}' in (TEMPLATES_DIR / document).read_text(encoding="utf-8")


def test_research_pdf_header_shows_no_updated_date():
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    rendered = env.get_template("research.html").render(
        title="Probe", topic="Other topic", as_of="2026-11-05", body_html="", evidence_items=[]
    )

    assert "Updated:" not in rendered
    assert "2026-11-05" not in rendered
    assert "Other topic" not in rendered


def test_research_pdf_has_no_references_page_or_dangling_citations(tmp_path, monkeypatch):
    captured = {}

    class FakeRenderer:
        async def render_html_to_pdf(self, html_content):
            captured["html"] = html_content
            return b"%PDF-fake"

    monkeypatch.setattr("app.integrations.pdf.playwright_renderer.PlaywrightPDFRenderer", FakeRenderer)
    monkeypatch.setitem(
        sys.modules,
        "app.integrations.storage.minio_client",
        SimpleNamespace(storage_service=MagicMock()),
    )
    job = SimpleNamespace(
        topic="What the user typed",
        plan_json={"blog_title": "Probe"},
        image_specs_json=None,
        pdf_url=None,
        final_markdown=(
            "# Probe\n\nCaching helps [Source](https://a.example/x). Queues too ([Source](https://b.example)). "
            "Retries matter (Source). See [Raft Paper](https://raft.example/paper) for details.\n"
        ),
        evidence_json=[{"title": "Evidence Title", "url": "https://raft.example/paper"}],
    )
    service = SimpleNamespace(repo=MagicMock(), _get_job_dir=lambda job_id: tmp_path)
    service.repo.get_by_id.return_value = job

    asyncio.run(ResearchService.get_pdf_file(service, "job-1"))
    html = captured["html"]

    assert "What the user typed" not in html
    assert "References" not in html
    assert "Evidence Title" not in html
    assert "<sup>" not in html
    assert "Source" not in html
    assert "Caching helps. Queues too. Retries matter." in html
    assert '<a href="https://raft.example/paper">Raft Paper</a>' in html


def test_research_pdf_turns_mermaid_fences_into_escaped_diagram_boxes(tmp_path, monkeypatch):
    captured = {}

    class FakeRenderer:
        async def render_html_to_pdf(self, html_content):
            captured["html"] = html_content
            return b"%PDF-fake"

    monkeypatch.setattr("app.integrations.pdf.playwright_renderer.PlaywrightPDFRenderer", FakeRenderer)
    monkeypatch.setitem(
        sys.modules,
        "app.integrations.storage.minio_client",
        SimpleNamespace(storage_service=MagicMock()),
    )
    job = SimpleNamespace(
        topic="Probe",
        plan_json={"blog_title": "Probe"},
        image_specs_json=[{"kind": "mermaid", "filename": "a.png"}],
        pdf_url=None,
        final_markdown=(
            '# Probe\n\nIntro.\n\n```mermaid\nflowchart TD\n    A["x < y"] --> B["*not italic*"]\n```\n*The caption*\n\n'
            "After.\n\n```python\nprint(1)\n```\n"
        ),
        evidence_json=[],
    )
    service = SimpleNamespace(repo=MagicMock(), _get_job_dir=lambda job_id: tmp_path)
    service.repo.get_by_id.return_value = job

    asyncio.run(ResearchService.get_pdf_file(service, "job-2"))
    html = captured["html"]

    assert '<div class="mermaid-canvas">flowchart TD' in html
    assert "x &lt; y" in html
    assert "--&gt;" in html
    assert "*not italic*" in html
    assert '<div class="diagram-caption">The caption</div>' in html
    assert "MERMAIDDIAGRAM" not in html
    assert "language-mermaid" not in html
    assert "print(1)" in html
    assert "<script>" in html.split("</head>")[0]
