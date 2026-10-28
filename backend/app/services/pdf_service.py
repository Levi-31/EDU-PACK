import os
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader

from app.core.config import settings
from app.core.exceptions import PDFGenerationException
from app.domain.enums import ArtifactType
from app.domain.schemas.artifact import ArtifactSchema
from app.domain.schemas.playlist import GenerationOptions
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
            consolidated_flashcards = []
            consolidated_glossary = []
            seen_glossary_terms = set()

            completed_count = 0
            for v in sorted_videos:
                has_notes = v.notes is not None
                if has_notes:
                    completed_count += 1
                    # Collect flashcards for consolidated revision
                    if v.notes.flashcards:
                        consolidated_flashcards.extend(v.notes.flashcards[:3])
                    # Collect glossary items
                    if v.notes.glossary:
                        for g in v.notes.glossary:
                            if g.term.lower() not in seen_glossary_terms:
                                seen_glossary_terms.add(g.term.lower())
                                consolidated_glossary.append(g)

                chapters_data.append({
                    "position": v.original_position,
                    "title": v.title,
                    "channel_title": v.channel_title,
                    "duration_formatted": f"{v.duration_seconds // 60}:{v.duration_seconds % 60:02d}" if v.duration_seconds else "--:--",
                    "video_url": v.video_url,
                    "thumbnail_url": v.thumbnail_url,
                    "is_available": v.is_available,
                    "has_notes": has_notes,
                    "failure_reason": v.failure_reason,
                    "notes": v.notes,
                    "visual": v.visual,
                    "is_mock": v.notes.is_mock if v.notes else False
                })

            # 3. Render HTML via Jinja2
            template = self.jinja_env.get_template("base.html")
            html_content = template.render(
                playlist={
                    "title": playlist_title,
                    "playlist_url": playlist_url,
                    "channel_name": channel_name,
                    "description": f"Curated technical notes from {channel_name or 'the instructor'} across {len(sorted_videos)} ordered video lectures."
                },
                job={"id": job_id},
                chapters=chapters_data,
                completed_count=completed_count,
                total_count=len(sorted_videos),
                generation_date=datetime.utcnow().strftime("%B %d, %Y"),
                consolidated_flashcards=consolidated_flashcards,
                consolidated_glossary=consolidated_glossary,
                css_styles=css_styles
            )

            # 4. Render to PDF bytes
            try:
                pdf_bytes = await self.renderer.render_html_to_pdf(html_content)
            except Exception as e:
                logger.warning(f"Primary PDF renderer failed ({e}), falling back to ReportLab...")
                fallback_renderer = ReportLabFallbackRenderer()
                pdf_bytes = await fallback_renderer.render_html_to_pdf(html_content)

            # 5. Save to Storage
            clean_title = "".join(c if c.isalnum() else "_" for c in playlist_title[:30])
            file_name = f"Playlist_Scholar_{clean_title}_{job_id[:8]}.pdf"
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

