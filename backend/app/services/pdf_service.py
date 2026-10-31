import os
import re
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from jinja2 import Environment, FileSystemLoader

try:
    import markdown
except ImportError:
    markdown = None

from app.core.config import settings
from app.core.exceptions import PDFGenerationException
from app.domain.enums import ArtifactType
from app.domain.schemas.artifact import ArtifactSchema
from app.domain.schemas.playlist import GenerationOptions
from app.domain.schemas.notes import GlossaryItem, Flashcard
from app.agents.state import VideoGraphItem
from app.integrations.pdf.renderer import PDFRendererInterface
from app.integrations.pdf.playwright_renderer import PlaywrightPDFRenderer
from app.integrations.pdf.reportlab_renderer import ReportLabFallbackRenderer
from app.integrations.storage.base import StorageProvider
from app.integrations.storage.local_storage import LocalStorageProvider
from app.db.session import SessionLocal
from app.db.repositories.artifact_repository import ArtifactRepository
from app.db.models.artifact import Artifact

logger = logging.getLogger(__name__)


def _render_markdown(text: Optional[str]) -> str:
    if not text:
        return ""
    if markdown:
        try:
            return markdown.markdown(text, extensions=["tables", "fenced_code", "nl2br"])
        except Exception:
            pass
    # Fallback basic formatting
    return text.replace("\n", "<br/>")


def _normalize_glossary(raw_items: List[GlossaryItem]) -> List[GlossaryItem]:
    """
    Normalizes and consolidates duplicate or overlapping glossary items (e.g. 'GCP',
    'Google Cloud Platform (GCP)', 'IAM', 'Identity and Access Management (IAM)', 'HA').
    Selects the most comprehensive definition and returns an alphabetically sorted list.
    """
    KNOWN_CANONICAL_SYNONYMS = {
        "iam": "Identity and Access Management (IAM)",
        "identity and access management": "Identity and Access Management (IAM)",
        "identity and access management (iam)": "Identity and Access Management (IAM)",
        "gcp": "Google Cloud Platform (GCP)",
        "google cloud platform": "Google Cloud Platform (GCP)",
        "google cloud platform (gcp)": "Google Cloud Platform (GCP)",
        "google cloud": "Google Cloud Platform (GCP)",
        "vpc": "Virtual Private Cloud (VPC)",
        "virtual private cloud": "Virtual Private Cloud (VPC)",
        "virtual private cloud (vpc)": "Virtual Private Cloud (VPC)",
        "gke": "Google Kubernetes Engine (GKE)",
        "google kubernetes engine": "Google Kubernetes Engine (GKE)",
        "google kubernetes engine (gke)": "Google Kubernetes Engine (GKE)",
        "gcs": "Google Cloud Storage (GCS)",
        "google cloud storage": "Google Cloud Storage (GCS)",
        "google cloud storage (gcs)": "Google Cloud Storage (GCS)",
        "cli": "Command Line Interface (CLI)",
        "command line interface": "Command Line Interface (CLI)",
        "command-line interface": "Command Line Interface (CLI)",
        "command line interface (cli)": "Command Line Interface (CLI)",
        "ha": "High Availability (HA)",
        "high availability": "High Availability (HA)",
        "high availability (ha)": "High Availability (HA)",
        "vm": "Virtual Machine (VM)",
        "virtual machine": "Virtual Machine (VM)",
        "virtual machines": "Virtual Machine (VM)",
        "nat": "Network Address Translation (NAT)",
        "network address translation": "Network Address Translation (NAT)",
        "network address translation (nat)": "Network Address Translation (NAT)",
        "dockerfile": "Dockerfile",
        "api": "Application Programming Interface (API)",
        "application programming interface": "Application Programming Interface (API)",
    }

    canonical_map: Dict[str, GlossaryItem] = {}

    for item in raw_items:
        clean_term = item.term.strip()
        lower_term = clean_term.lower()

        canonical_name = KNOWN_CANONICAL_SYNONYMS.get(lower_term)
        if not canonical_name:
            match = re.search(r"\(([A-Za-z0-9]+)\)", clean_term)
            if match:
                acronym = match.group(1).lower()
                canonical_name = KNOWN_CANONICAL_SYNONYMS.get(acronym, clean_term)
            else:
                canonical_name = clean_term

        canon_key = canonical_name.lower()
        if canon_key not in canonical_map:
            canonical_map[canon_key] = GlossaryItem(
                term=canonical_name,
                definition=item.definition.strip()
            )
        else:
            existing = canonical_map[canon_key]
            if len(item.definition.strip()) > len(existing.definition):
                existing.definition = item.definition.strip()
            if "(" in canonical_name and "(" not in existing.term:
                existing.term = canonical_name

    return sorted(list(canonical_map.values()), key=lambda x: x.term.lower())


def _deduplicate_flashcards(raw_cards: List[Flashcard]) -> List[Flashcard]:
    seen_q: Set[str] = set()
    deduped: List[Flashcard] = []
    for c in raw_cards:
        norm_q = re.sub(r"[^a-zA-Z0-9]", "", c.question.lower())
        if norm_q not in seen_q:
            seen_q.add(norm_q)
            deduped.append(c)
    return deduped


def clean_technical_title(raw_title: str, playlist_title: Optional[str] = None) -> str:
    """
    Cleans repetitive YouTube noise, series tags, and channel watermarks to produce
    a concise, professional technical handbook chapter title.
    """
    if not raw_title:
        return ""
    t = raw_title.strip()

    # 1. Strip repetitive channel watermarks
    t = re.sub(r"(?i)\s*[\-|\•]\s*CampusX\b", "", t)
    t = re.sub(r"(?i)\s*\|\s*CampusX\b", "", t)
    t = re.sub(r"(?i)\s*by\s+[A-Za-z0-9_\s]+$", "", t)

    # 2. Strip playlist/series tags if present
    series_patterns = [
        r"(?i)\s*\|\s*MCP\s+Trilogy\b",
        r"(?i)\s*\|\s*Mini\s+Playlist\b",
        r"(?i)\s*\|\s*Agentic\s+AI\s+using\s+LangGraph\b",
        r"(?i)\s*\|\s*LangGraph\s+Tutorial\b",
        r"(?i)\s*\|\s*GCP\s+Zero\s+to\s+Hero\b",
        r"(?i)\s*\|\s*Video\s+\d+\b",
        r"(?i)\s*\|\s*Lecture\s+\d+\b",
        r"(?i)^Day[\-\s]*\d+\s*\|\s*",
        r"(?i)^Lecture[\-\s]*\d+\s*\|\s*",
    ]
    for sp in series_patterns:
        t = re.sub(sp, "", t)

    # 3. Clean up MCP-specific titles cleanly matching standard chapter titles
    if re.search(r"(?i)\bModel Context Protocol\b", t) and (t.strip() == "Model Context Protocol" or "mini playlist" in raw_title.lower()):
        t = "Model Context Protocol — Introduction"
    elif re.search(r"(?i)^Model Context Protocol\s*-\s*The Why$", t):
        t = "Why Model Context Protocol?"
    elif "How to connect MCP Servers" in t or "The How | How to connect" in raw_title:
        t = "Connecting MCP Servers"
    elif re.search(r"(?i)How to Build Local MCP Servers", t):
        t = "Building Local MCP Servers"
    elif re.search(r"(?i)How to Build & Deploy Remote MCP Servers", t) or "Deploying Remote MCP Servers" in t:
        t = "Deploying Remote MCP Servers"
    elif re.search(r"(?i)How to build MCP Clients", t):
        t = "Building MCP Clients"
    elif "MCP Architecture | Model Context Protocol Architecture" in raw_title:
        t = "MCP Architecture"

    # 4. Remove duplicate segments separated by pipe (e.g. "MCP Architecture | Model Context Protocol Architecture")
    parts = [p.strip() for p in t.split("|") if p.strip()]
    if len(parts) > 1:
        first, second = parts[0], parts[1]
        if first.lower() in second.lower() or second.lower() in first.lower():
            t = first if len(first) <= len(second) else second
        else:
            t = parts[0]

    return t.strip()


def extract_destination_page_numbers(pdf_bytes: bytes) -> Dict[str, int]:
    """
    Extracts 1-indexed destination page numbers from the rendered Chromium PDF bytes.
    Matches PDF destination objects: /chapter-1, /final-revision, etc.
    """
    page_matches = list(re.finditer(rb'(\d+)\s+0\s+obj\s*<<[^\>]*?/Type\s*/Page\b', pdf_bytes))
    obj_to_page = {int(m.group(1)): i for i, m in enumerate(page_matches, 1)}

    dest_matches = re.finditer(rb'/([a-zA-Z0-9_\-]+)\s*\[\s*(\d+)\s+0\s+R', pdf_bytes)
    results = {}
    for dm in dest_matches:
        name = dm.group(1).decode('ascii', errors='ignore')
        obj_id = int(dm.group(2))
        if obj_id in obj_to_page:
            results[name] = obj_to_page[obj_id]
    return results


def _clean_citation_title(val: str) -> str:
    """Strips leading emojis, icons, or symbols from citation and reference titles."""
    if not val:
        return ""
    # Strip leading emojis, non-ascii symbols, bullets, or punctuation from title start
    cleaned = re.sub(r'^[^\w\(\[\{\'\"]+', '', val).strip()
    return cleaned if cleaned else val


class PDFService:
    def __init__(
        self,
        renderer: Optional[PDFRendererInterface] = None,
        storage: Optional[StorageProvider] = None
    ):
        self.storage = storage or LocalStorageProvider()
        if renderer:
            self.renderer = renderer
        elif settings.PDF_RENDERER == "playwright":
            self.renderer = PlaywrightPDFRenderer()
        else:
            self.renderer = ReportLabFallbackRenderer()

        template_dir = Path(__file__).resolve().parent.parent / "templates" / "pdf"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )
        self.jinja_env.filters["markdown"] = _render_markdown
        self.jinja_env.filters["clean_title"] = _clean_citation_title

        # Load local Mermaid JS for offline diagram rendering
        mermaid_path = Path(__file__).resolve().parent.parent / "static" / "js" / "mermaid.min.js"
        if mermaid_path.exists():
            self.mermaid_js = mermaid_path.read_text(encoding="utf-8")
        else:
            self.mermaid_js = ""

    async def compile_playlist_pdf(
        self,
        job_id: str,
        playlist_title: str,
        playlist_url: str,
        channel_name: Optional[str],
        videos: List[VideoGraphItem],
        options: GenerationOptions
    ) -> ArtifactSchema:
        """
        Compiles all video chapters in their exact original playlist sequence into a polished PDF document.
        Validates the artifact post-generation.
        """
        try:
            # 1. Read CSS styles
            css_path = Path(__file__).resolve().parent.parent / "templates" / "pdf" / "styles.css"
            css_styles = css_path.read_text(encoding="utf-8") if css_path.exists() else ""

            # 2. Prepare ordered chapters
            sorted_videos = sorted(videos, key=lambda v: v.original_position)
            chapters_data = []
            raw_flashcards = []
            raw_glossary = []

            completed_count = 0
            for v in sorted_videos:
                has_notes = v.notes is not None
                if has_notes:
                    completed_count += 1
                    # Clean emojis and icons from citation titles
                    if v.notes.all_sources:
                        for s in v.notes.all_sources:
                            if hasattr(s, "title") and s.title:
                                s.title = _clean_citation_title(s.title)
                            elif isinstance(s, dict) and s.get("title"):
                                s["title"] = _clean_citation_title(s["title"])
                    if v.notes.sections:
                        for sec in v.notes.sections:
                            if getattr(sec, "cited_sources", None):
                                for s in sec.cited_sources:
                                    if hasattr(s, "title") and s.title:
                                        s.title = _clean_citation_title(s.title)
                                    elif isinstance(s, dict) and s.get("title"):
                                        s["title"] = _clean_citation_title(s["title"])

                    # Collect flashcards for consolidated revision
                    if v.notes.flashcards:
                        raw_flashcards.extend(v.notes.flashcards[:3])
                    # Collect glossary items
                    if v.notes.glossary:
                        raw_glossary.extend(v.notes.glossary)

                # Ensure visual asset is extracted from note sections if not directly on item
                visual_asset = v.visual
                if not visual_asset and v.notes and v.notes.sections:
                    for s in v.notes.sections:
                        if getattr(s, "visual", None) and getattr(s.visual, "mermaid_code", None):
                            visual_asset = s.visual
                            break

                chapters_data.append({
                    "position": v.original_position,
                    "title": v.title,
                    "clean_title": clean_technical_title(v.title, playlist_title),
                    "channel_title": v.channel_title,
                    "duration_formatted": f"{v.duration_seconds // 60}:{v.duration_seconds % 60:02d}" if v.duration_seconds else "--:--",
                    "video_url": v.video_url,
                    "thumbnail_url": v.thumbnail_url,
                    "is_available": v.is_available,
                    "has_notes": has_notes,
                    "failure_reason": v.failure_reason,
                    "notes": v.notes,
                    "visual": visual_asset,
                    "is_mock": v.notes.is_mock if v.notes else False,
                    "page_number": "--"
                })

            consolidated_glossary = _normalize_glossary(raw_glossary)
            consolidated_flashcards = _deduplicate_flashcards(raw_flashcards)

            # 3. Helper to render HTML with specific calculated page numbers
            def _render_document_html(page_mapping: Optional[Dict[str, int]] = None) -> str:
                if page_mapping:
                    for idx, ch in enumerate(chapters_data, 1):
                        p = page_mapping.get(f"chapter-{idx}")
                        ch["page_number"] = f"{p:02d}" if p is not None else "--"
                    rev_p = page_mapping.get("final-revision")
                    rev_page_str = f"{rev_p:02d}" if rev_p is not None else "--"
                else:
                    rev_page_str = "--"

                tpl = self.jinja_env.get_template("base.html")
                return tpl.render(
                    playlist={
                        "title": playlist_title,
                        "playlist_url": playlist_url,
                        "channel_name": channel_name,
                        "description": f"Comprehensive technical reference handbook and deep curriculum notes synthesized across {len(sorted_videos)} ordered video lectures."
                    },
                    job={"id": job_id},
                    chapters=chapters_data,
                    review_page_number=rev_page_str,
                    completed_count=completed_count,
                    total_count=len(sorted_videos),
                    generation_date=datetime.utcnow().strftime("%B %d, %Y"),
                    consolidated_flashcards=consolidated_flashcards,
                    consolidated_glossary=consolidated_glossary,
                    css_styles=css_styles,
                    mermaid_js=self.mermaid_js
                )

            # Pass 1: Render with initial placeholders
            html_content = _render_document_html(page_mapping=None)

            # 4. Render to PDF bytes
            try:
                pdf_bytes = await self.renderer.render_html_to_pdf(html_content)
                # Pass 2: Extract exact destination page numbers and re-render if Playwright renderer
                if isinstance(self.renderer, PlaywrightPDFRenderer):
                    page_map = extract_destination_page_numbers(pdf_bytes)
                    if page_map and any(k.startswith("chapter-") for k in page_map):
                        logger.info("Pass 1 extracted page numbers: %s; executing Pass 2 pagination", page_map)
                        html_pass2 = _render_document_html(page_mapping=page_map)
                        pdf_bytes = await self.renderer.render_html_to_pdf(html_pass2)
            except Exception as e:
                logger.warning(f"Primary PDF renderer failed ({e}), falling back to ReportLab...")
                fallback_renderer = ReportLabFallbackRenderer()
                pdf_bytes = await fallback_renderer.render_html_to_pdf(html_content)

            # 5. Save to Storage
            clean_title = "".join(c if c.isalnum() else "_" for c in playlist_title[:30])
            file_name = f"{clean_title}_{job_id[:8]}.pdf"
            rel_storage_path = f"artifacts/{job_id}/{file_name}"

            abs_path, file_size, checksum = self.storage.save_bytes(
                relative_path=rel_storage_path,
                data=pdf_bytes,
                mime_type="application/pdf"
            )

            # 6. Artifact Validation
            if file_size <= 0:
                raise PDFGenerationException("Rendered PDF file size is 0 bytes.")
            if not os.path.exists(abs_path):
                raise PDFGenerationException("Rendered PDF file does not exist on disk.")

            # 7. Persist to DB
            artifact_id = str(uuid.uuid4())
            db = SessionLocal()
            try:
                repo = ArtifactRepository(db)
                artifact_model = Artifact(
                    id=artifact_id,
                    job_id=job_id,
                    artifact_type=ArtifactType.PDF_NOTES.value,
                    file_name=file_name,
                    file_path=abs_path,
                    mime_type="application/pdf",
                    file_size_bytes=file_size,
                    checksum_sha256=checksum,
                    is_valid=True
                )
                repo.create(artifact_model)
            finally:
                db.close()

            return ArtifactSchema(
                id=artifact_id,
                job_id=job_id,
                artifact_type=ArtifactType.PDF_NOTES,
                file_name=file_name,
                file_path=abs_path,
                mime_type="application/pdf",
                file_size_bytes=file_size,
                checksum_sha256=checksum,
                created_at=datetime.utcnow(),
                download_url=f"/api/v1/jobs/{job_id}/download",
                is_valid=True
            )

        except Exception as e:
            logger.error(f"Error compiling PDF: {e}", exc_info=True)
            raise PDFGenerationException(f"PDF compilation failed: {str(e)}")
