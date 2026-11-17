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
from app.integrations.pdf.renderer import PDFRendererInterface, fit_heading
from app.integrations.pdf.playwright_renderer import PlaywrightPDFRenderer
from app.integrations.pdf.reportlab_renderer import ReportLabFallbackRenderer
from app.integrations.storage.base import StorageProvider
from app.integrations.storage.local_storage import LocalStorageProvider
from app.db.session import SessionLocal
from app.db.repositories.artifact_repository import ArtifactRepository
from app.db.models.artifact import Artifact

logger = logging.getLogger(__name__)

COVER_TEXT_WIDTH_PT = 453  # A4 width minus the cover's 25mm side padding


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
    Normalizes and consolidates duplicate or overlapping glossary items across chapters.
    Dynamically identifies acronyms and their full expansions (e.g., 'RAG' vs
    'Retrieval-Augmented Generation (RAG)', 'IAM' vs 'Identity and Access Management (IAM)')
    directly from the content without relying on brittle domain-specific hardcoded dictionaries.
    Selects the most comprehensive definition and returns an alphabetically sorted list.
    """
    if not raw_items:
        return []

    # 1. First pass: dynamically discover canonical expansions and acronyms from the terms themselves
    alias_to_canonical: Dict[str, str] = {}

    for item in raw_items:
        clean = item.term.strip()
        # Case A: "Full Term Name (ACRONYM)" e.g. "Identity and Access Management (IAM)"
        match_abbr = re.match(r"^(.+?)\s*\(([A-Za-z0-9\-_\s]+)\)$", clean)
        if match_abbr:
            full_name = match_abbr.group(1).strip()
            abbr = match_abbr.group(2).strip()
            canonical = clean
            alias_to_canonical[clean.lower()] = canonical
            alias_to_canonical[abbr.lower()] = canonical
            alias_to_canonical[full_name.lower()] = canonical
            continue

        # Case B: "ACRONYM (Full Term Name)" e.g. "IAM (Identity and Access Management)"
        match_reverse = re.match(r"^([A-Za-z0-9\-_]{2,10})\s*\((.+?)\)$", clean)
        if match_reverse:
            abbr = match_reverse.group(1).strip()
            full_name = match_reverse.group(2).strip()
            canonical = f"{full_name} ({abbr})"
            alias_to_canonical[clean.lower()] = canonical
            alias_to_canonical[abbr.lower()] = canonical
            alias_to_canonical[full_name.lower()] = canonical

    # 2. Second pass: group and merge definitions
    canonical_map: Dict[str, GlossaryItem] = {}

    for item in raw_items:
        term_clean = item.term.strip()
        lower_term = term_clean.lower()
        def_clean = item.definition.strip()

        # Resolve to discovered canonical name, or fallback to clean term
        canonical_name = alias_to_canonical.get(lower_term, term_clean)
        canon_key = canonical_name.lower()

        # Plural normalization if needed (e.g. "virtual machines" -> "virtual machine")
        if canon_key.endswith("s") and not canon_key.endswith("ss") and len(canon_key) > 4:
            singular_key = canon_key[:-1]
            if singular_key in canonical_map:
                canon_key = singular_key

        if canon_key not in canonical_map:
            canonical_map[canon_key] = GlossaryItem(
                term=canonical_name,
                definition=def_clean
            )
        else:
            existing = canonical_map[canon_key]
            # Retain the longer, more comprehensive definition
            if len(def_clean) > len(existing.definition):
                existing.definition = def_clean
            # Prefer term with acronym expansion or proper capitalization
            if "(" in canonical_name and "(" not in existing.term:
                existing.term = canonical_name
            elif existing.term.islower() and not canonical_name.islower():
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
        r"(?i)\s*\|\s*Mini\s+Playlist\b",
        r"(?i)\s*\|\s*Video\s+\d+\b",
        r"(?i)\s*\|\s*Lecture\s+\d+\b",
        r"(?i)^Day[\-\s]*\d+\s*\|\s*",
        r"(?i)^Lecture[\-\s]*\d+\s*\|\s*",
    ]
    for sp in series_patterns:
        t = re.sub(sp, "", t)

    # 3. Remove duplicate segments separated by pipe
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
            total_count = len(sorted_videos)
            completed_count = sum(1 for v in sorted_videos if v.notes is not None)
            is_single_video = (total_count == 1)

            # Defensive threshold check: Do not generate PDF if requirements are not met
            if is_single_video and completed_count == 0:
                raise PDFGenerationException(
                    "Transcript is unavailable for this video. PDF generation cannot proceed as captions or transcripts are required."
                )

            if not is_single_video and (completed_count / max(total_count, 1)) < 0.50:
                unavailable_count = total_count - completed_count
                avail_pct = round((completed_count / max(total_count, 1)) * 100)
                raise PDFGenerationException(
                    f"Transcripts are unavailable for the majority of videos in this playlist "
                    f"({unavailable_count}/{total_count} unavailable, {avail_pct}% available). "
                    f"PDF generation has been aborted as at least 50% transcript availability is required."
                )

            chapters_data = []
            raw_flashcards = []
            raw_glossary = []

            for idx, v in enumerate(sorted_videos, 1):
                has_notes = v.notes is not None
                if has_notes:
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

                # Ensure visual asset is extracted from item, notes, or sections
                visual_asset = v.visual
                if not visual_asset and v.notes:
                    if getattr(v.notes, "visual", None):
                        visual_asset = v.notes.visual
                    elif getattr(v.notes, "sections", None):
                        for s in v.notes.sections:
                            if getattr(s, "visual", None):
                                visual_asset = s.visual
                                break

                chapters_data.append({
                    "position": v.original_position,
                    "chapter_idx": idx,
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
                    for ch in chapters_data:
                        if ch["has_notes"] and ch["is_available"]:
                            p = page_mapping.get(f"chapter-{ch['chapter_idx']}")
                            ch["page_number"] = f"{p:02d}" if p is not None else "--"
                        else:
                            ch["page_number"] = "--"
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
                        "description": (
                            f"Comprehensive technical reference handbook and deep curriculum notes synthesized across {len(sorted_videos)} ordered video lectures."
                            if len(sorted_videos) > 1 else
                            f"Standalone technical reference and comprehensive lecture notes synthesized from {playlist_title}."
                        )
                    },
                    cover_heading=fit_heading(playlist_title, width_pt=COVER_TEXT_WIDTH_PT, max_pt=28),
                    job={"id": job_id},
                    chapters=chapters_data,
                    review_page_number=rev_page_str,
                    completed_count=completed_count,
                    total_count=len(sorted_videos),
                    is_single_video=(len(sorted_videos) == 1),
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

            # Upload to MinIO object storage
            minio_url = None
            try:
                from app.integrations.storage.minio_client import storage_service
                obj_name = f"notes/{job_id}/{file_name}"
                minio_url = storage_service.upload_bytes(pdf_bytes, obj_name, content_type="application/pdf")
            except Exception as ex:
                logger.warning(f"Could not upload YouTube PDF to MinIO: {ex}")

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
                    file_url=minio_url,
                    mime_type="application/pdf",
                    file_size_bytes=file_size,
                    checksum_sha256=checksum,
                    is_valid=True
                )
                repo.create(artifact_model)

                # Also update PlaylistJob.pdf_url
                from app.db.models.job import PlaylistJob
                job = db.query(PlaylistJob).filter(PlaylistJob.id == job_id).first()
                if job:
                    job.pdf_url = minio_url
                    db.commit()
            finally:
                db.close()

            return ArtifactSchema(
                id=artifact_id,
                job_id=job_id,
                artifact_type=ArtifactType.PDF_NOTES,
                file_name=file_name,
                file_path=abs_path,
                file_url=minio_url,
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
