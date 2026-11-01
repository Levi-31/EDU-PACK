import os
import json
import asyncio
import zipfile
import logging
from io import BytesIO
from pathlib import Path
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import PlaylistScholarException
from app.db.models.research_job import ResearchJob
from app.db.repositories.research_job_repository import ResearchJobRepository
from app.domain.schemas.research_module import (
    CreateResearchJobRequest,
    ResearchJobDetailResponse,
    ResearchJobListResponse
)
from app.modules.research.graph import app as research_graph
from app.modules.research.models import State

logger = logging.getLogger(__name__)


def safe_slug(title: str) -> str:
    import re
    s = title.strip().lower()
    s = re.sub(r"[^a-z0-9 _-]+", "", s)
    s = re.sub(r"\s+", "_", s).strip("_")
    return s or "research"


def bundle_zip(md_text: str, md_filename: str, images_dir: Path) -> bytes:
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(md_filename, md_text.encode("utf-8"))
        if images_dir.exists() and images_dir.is_dir():
            for p in images_dir.rglob("*"):
                if p.is_file():
                    z.write(p, arcname=f"images/{p.name}")
    return buf.getvalue()


class ResearchService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ResearchJobRepository(db)

    def _get_job_dir(self, job_id: str) -> Path:
        d = settings.artifacts_path / f"research_{job_id}"
        d.mkdir(parents=True, exist_ok=True)
        return d

    async def create_job(self, request: CreateResearchJobRequest) -> ResearchJobDetailResponse:
        as_of_val = request.as_of or datetime.utcnow().strftime("%Y-%m-%d")
        
        job = ResearchJob(
            topic=request.topic.strip(),
            as_of=as_of_val,
            mode="closed_book",
            status="QUEUED",
            current_stage="Queued",
            progress_percentage=0.0,
            is_mock=settings.DEMO_MODE,
            logs_json=[f"[{datetime.utcnow().isoformat()}] Research job registered: '{request.topic[:60]}'"]
        )
        created = self.repo.create(job)

        # Dispatch execution
        if settings.JOB_RUNNER == "celery":
            try:
                from app.workers.celery_app import execute_research_job
                execute_research_job.delay(created.id)
            except Exception as e:
                logger.warning(f"Failed to dispatch to Celery ({e}), falling back to background thread")
                asyncio.create_task(self.run_job_async(created.id))
        else:
            asyncio.create_task(self.run_job_async(created.id))

        return self.get_job_detail(created.id)

    async def run_job_async(self, job_id: str):
        # Run blocking execution in thread pool to not block event loop
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.execute_job_sync, job_id)

    def execute_job_sync(self, job_id: str):
        job = self.repo.get_by_id(job_id)
        if not job:
            logger.error(f"Research job {job_id} not found for execution.")
            return

        job_dir = self._get_job_dir(job_id)
        logs: List[str] = list(job.logs_json or [])
        
        def log(msg: str):
            timestamp = datetime.utcnow().strftime("%H:%M:%S")
            entry = f"[{timestamp}] {msg}"
            logs.append(entry)
            logger.info(f"[Research-{job_id[:8]}] {msg}")

        try:
            job.status = "RUNNING"
            job.current_stage = "Understanding topic & deciding research strategy"
            job.progress_percentage = 10.0
            self.db.commit()

            log(f"Starting research workflow for topic: '{job.topic}' (As-of: {job.as_of})")

            inputs: Dict[str, Any] = {
                "topic": job.topic,
                "mode": "",
                "needs_research": False,
                "queries": [],
                "evidence": [],
                "plan": None,
                "as_of": job.as_of,
                "recency_days": 7,
                "sections": [],
                "merged_md": "",
                "md_with_placeholders": "",
                "image_specs": [],
                "final": "",
                "output_dir": str(job_dir),
            }

            current_state: Dict[str, Any] = {}
            # Stream execution for real stage tracking
            for update in research_graph.stream(inputs, stream_mode="updates"):
                if isinstance(update, dict):
                    node_name = next(iter(update.keys()))
                    payload = update[node_name]
                    current_state.update(payload if isinstance(payload, dict) else {})
                    
                    if node_name == "router":
                        mode = payload.get("mode", "closed_book")
                        needs = payload.get("needs_research", False)
                        log(f"Router decision: mode='{mode}', needs_research={needs}")
                        self.repo.update_stage(
                            job_id,
                            stage=f"Strategy: {mode.upper()} - Gathering evidence" if needs else f"Strategy: {mode.upper()} - Planning article",
                            progress=25.0 if needs else 40.0,
                            mode=mode,
                            log_entry=f"Routing decided: {mode} ({'search active' if needs else 'closed book'})"
                        )
                    elif node_name == "research":
                        ev_count = len(payload.get("evidence", []))
                        log(f"Evidence gathering complete: {ev_count} verified sources retrieved")
                        self.repo.update_stage(
                            job_id,
                            stage="Building comprehensive article plan",
                            progress=45.0,
                            log_entry=f"Gathered {ev_count} authoritative evidence sources"
                        )
                    elif node_name == "orchestrator":
                        plan_obj = payload.get("plan")
                        task_count = len(plan_obj.tasks) if plan_obj and hasattr(plan_obj, "tasks") else 0
                        log(f"Article plan built: '{getattr(plan_obj, 'blog_title', 'Untitled')}' with {task_count} sections")
                        self.repo.update_stage(
                            job_id,
                            stage=f"Writing {task_count} sections concurrently",
                            progress=60.0,
                            log_entry=f"Outline constructed with {task_count} parallel tasks"
                        )
                    elif node_name == "worker":
                        log("Section writer task completed")
                        self.repo.update_stage(
                            job_id,
                            stage="Writing content sections",
                            progress=75.0,
                            log_entry="Section drafting completed"
                        )
                    elif node_name == "reducer":
                        log("Content merged and images generated")
                        self.repo.update_stage(
                            job_id,
                            stage="Finalizing markdown and image assets",
                            progress=90.0,
                            log_entry="Merged content and placed images"
                        )

            # Final state already collected from streaming graph updates
            # Extract outputs
            final_md = current_state.get("final") or current_state.get("merged_md") or ""

            plan_obj = current_state.get("plan")
            plan_dict = plan_obj.model_dump() if hasattr(plan_obj, "model_dump") else (plan_obj or {})
            blog_title = plan_dict.get("blog_title", job.topic) if isinstance(plan_dict, dict) else job.topic

            evidence_items = current_state.get("evidence", []) or []
            evidence_list = [
                e.model_dump() if hasattr(e, "model_dump") else e
                for e in evidence_items
            ]

            image_specs = current_state.get("image_specs", []) or []
            sections_list = current_state.get("sections", []) or []

            # Save Markdown file
            md_filename = f"{safe_slug(blog_title)}.md"
            md_path = job_dir / md_filename
            md_path.write_text(final_md, encoding="utf-8")

            # Generate ZIP bundle (MD + images)
            bundle_filename = f"{safe_slug(blog_title)}_bundle.zip"
            bundle_bytes = bundle_zip(final_md, md_filename, job_dir / "images")
            bundle_path = job_dir / bundle_filename
            bundle_path.write_bytes(bundle_bytes)

            log("Research synthesis complete. Markdown and bundle generated successfully.")

            # Upload generated assets to MinIO object storage
            minio_image_urls: List[str] = []
            images_dir = job_dir / "images"
            if images_dir.exists():
                from app.integrations.storage.minio_client import storage_service
                for img_file in sorted(images_dir.glob("*.png")):
                    try:
                        u = storage_service.upload_file(
                            img_file,
                            f"research/{job_id}/images/{img_file.name}",
                            content_type="image/png"
                        )
                        minio_image_urls.append(u)
                    except Exception as err:
                        logger.warning(f"MinIO image upload error for {img_file.name}: {err}")

            bundle_minio_url = None
            markdown_minio_url = None
            try:
                from app.integrations.storage.minio_client import storage_service
                bundle_minio_url = storage_service.upload_file(
                    bundle_path,
                    f"research/{job_id}/{bundle_filename}",
                    content_type="application/zip"
                )
                markdown_minio_url = storage_service.upload_file(
                    md_path,
                    f"research/{job_id}/{md_filename}",
                    content_type="text/markdown"
                )
            except Exception as err:
                logger.warning(f"MinIO bundle/markdown upload error: {err}")

            self.repo.complete_job(
                job_id=job_id,
                mode=current_state.get("mode", "closed_book"),
                plan_dict=plan_dict,
                evidence_list=evidence_list,
                sections_list=sections_list,
                image_specs=image_specs,
                final_markdown=final_md,
                markdown_filename=md_filename,
                bundle_filename=bundle_filename,
                images_dir_path=str(job_dir / "images"),
                logs=logs,
                bundle_url=bundle_minio_url,
                markdown_url=markdown_minio_url,
                image_urls_json=minio_image_urls
            )

            # Auto-render PDF and upload to MinIO in isolated thread with safety timeout
            try:
                import concurrent.futures
                log("Rendering publication-grade PDF and uploading to MinIO object storage...")
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    pool.submit(lambda: asyncio.run(self.get_pdf_file(job_id))).result(timeout=15.0)
                log("Publication-grade PDF successfully uploaded to MinIO.")
            except Exception as pdf_err:
                logger.debug(f"Pre-rendering PDF note for {job_id}: {pdf_err}")

        except Exception as e:
            logger.exception(f"Research job {job_id} failed: {e}")
            log(f"Execution failed with error: {str(e)}")
            try:
                self.db.rollback()
                self.repo.fail_job(job_id, error_message=str(e), logs=logs)
            except Exception as repo_err:
                logger.error(f"Failed to record failure state for job {job_id}: {repo_err}")

    def get_job_detail(self, job_id: str) -> ResearchJobDetailResponse:
        job = self.repo.get_by_id(job_id)
        if not job:
            raise PlaylistScholarException(f"Research job '{job_id}' not found.", status_code=404)

        # Collect generated image filenames
        images: List[str] = []
        if job.images_dir_path:
            img_dir = Path(job.images_dir_path)
            if img_dir.exists() and img_dir.is_dir():
                images = [p.name for p in sorted(img_dir.iterdir()) if p.is_file() and p.stat().st_size > 0]

        return ResearchJobDetailResponse(
            id=job.id,
            topic=job.topic,
            as_of=job.as_of,
            mode=job.mode,
            status=job.status,
            current_stage=job.current_stage,
            progress_percentage=job.progress_percentage,
            plan=job.plan_json,
            evidence=job.evidence_json or [],
            image_specs=job.image_specs_json or [],
            sections=job.sections_json or [],
            final_markdown=job.final_markdown,
            markdown_content=job.final_markdown,
            article_title=job.plan_json.get("blog_title") if (job.plan_json and isinstance(job.plan_json, dict)) else job.topic,
            markdown_filename=job.markdown_filename,
            bundle_filename=job.bundle_filename,
            pdf_url=job.pdf_url,
            bundle_url=job.bundle_url,
            markdown_url=job.markdown_url,
            images=images,
            image_urls=job.image_urls_json if (job.image_urls_json and len(job.image_urls_json) > 0) else [f"/api/v1/research/{job.id}/images/{img}" for img in images],
            logs=job.logs_json or [],
            error_message=job.error_message,
            error_summary=job.error_message,
            is_mock=job.is_mock,

            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at
        )

    def list_jobs(self, page: int = 1, page_size: int = 20) -> ResearchJobListResponse:
        skip = (page - 1) * page_size
        jobs, total = self.repo.list_jobs(skip=skip, limit=page_size)
        items = []
        for j in jobs:
            images = []
            if j.images_dir_path:
                img_dir = Path(j.images_dir_path)
                if img_dir.exists():
                    images = [p.name for p in sorted(img_dir.iterdir()) if p.is_file() and p.stat().st_size > 0]
            items.append(
                ResearchJobDetailResponse(
                    id=j.id,
                    topic=j.topic,
                    as_of=j.as_of,
                    mode=j.mode,
                    status=j.status,
                    current_stage=j.current_stage,
                    progress_percentage=j.progress_percentage,
                    plan=j.plan_json,
                    evidence=j.evidence_json or [],
                    image_specs=j.image_specs_json or [],
                    article_title=j.plan_json.get("blog_title") if (j.plan_json and isinstance(j.plan_json, dict)) else j.topic,
                    final_markdown=j.final_markdown,
                    markdown_content=j.final_markdown,
                    markdown_filename=j.markdown_filename,
                    bundle_filename=j.bundle_filename,
                    pdf_url=j.pdf_url,
                    bundle_url=j.bundle_url,
                    markdown_url=j.markdown_url,
                    images=images,
                    image_urls=j.image_urls_json if (j.image_urls_json and len(j.image_urls_json) > 0) else [f"/api/v1/research/{j.id}/images/{img}" for img in images],
                    logs=j.logs_json or [],
                    error_message=j.error_message,
                    is_mock=j.is_mock,
                    created_at=j.created_at,
                    updated_at=j.updated_at,
                    completed_at=j.completed_at
                )
            )
        return ResearchJobListResponse(jobs=items, total=total, page=page, page_size=page_size)

    def get_markdown_file(self, job_id: str) -> Tuple[bytes, str]:
        job = self.repo.get_by_id(job_id)
        if not job or not job.final_markdown:
            raise PlaylistScholarException(f"Markdown not available for job '{job_id}'", status_code=404)
        filename = job.markdown_filename or f"research_{job_id[:8]}.md"
        return job.final_markdown.encode("utf-8"), filename

    def get_bundle_file(self, job_id: str) -> Tuple[bytes, str]:
        job = self.repo.get_by_id(job_id)
        if not job or not job.final_markdown:
            raise PlaylistScholarException(f"Bundle not available for job '{job_id}'", status_code=404)
        job_dir = self._get_job_dir(job_id)
        bundle_path = job_dir / (job.bundle_filename or f"research_{job_id[:8]}_bundle.zip")
        if bundle_path.exists():
            return bundle_path.read_bytes(), bundle_path.name
        # Build dynamically if not already saved
        bundle_bytes = bundle_zip(job.final_markdown, job.markdown_filename or "article.md", job_dir / "images")
        return bundle_bytes, f"research_{job_id[:8]}_bundle.zip"

    def get_image_file(self, job_id: str, filename: str) -> Tuple[bytes, str]:
        job_dir = self._get_job_dir(job_id)
        img_path = job_dir / "images" / filename
        if not img_path.exists():
            raise PlaylistScholarException(f"Image '{filename}' not found for job '{job_id}'", status_code=404)
        content_type = "image/png"
        if filename.endswith(".jpg") or filename.endswith(".jpeg"):
            content_type = "image/jpeg"
        elif filename.endswith(".svg"):
            content_type = "image/svg+xml"
        return img_path.read_bytes(), content_type

    async def get_pdf_file(self, job_id: str) -> Tuple[bytes, str]:
        """
        Generates and returns an editorial publication-grade PDF using Playwright Chromium.
        Inlines local high-resolution images as base64 data URIs so all visuals render instantly.
        """
        job = self.repo.get_by_id(job_id)
        if not job or not job.final_markdown:
            raise PlaylistScholarException(f"Content not available for job '{job_id}'", status_code=404)

        job_dir = self._get_job_dir(job_id)
        blog_title = job.plan_json.get("blog_title", job.topic) if (job.plan_json and isinstance(job.plan_json, dict)) else job.topic
        pdf_filename = f"{safe_slug(blog_title)}.pdf"
        cached_pdf = job_dir / pdf_filename

        # If already compiled with high-res embedded figures (>350KB), ensure uploaded to MinIO and return cached
        if cached_pdf.exists() and cached_pdf.stat().st_size > 350000:
            if not job.pdf_url:
                try:
                    from app.integrations.storage.minio_client import storage_service
                    minio_pdf_url = storage_service.upload_file(
                        cached_pdf,
                        f"research/{job_id}/{pdf_filename}",
                        content_type="application/pdf"
                    )
                    self.repo.update_urls(job_id, pdf_url=minio_pdf_url)
                except Exception as up_err:
                    logger.warning(f"MinIO cached PDF upload note: {up_err}")
            return cached_pdf.read_bytes(), pdf_filename

        import re
        import base64
        import markdown
        from jinja2 import Environment, FileSystemLoader
        from app.integrations.pdf.playwright_renderer import PlaywrightPDFRenderer

        md_text = job.final_markdown
        images_dir = job_dir / "images"

        # Ensure planned images are embedded in md_text if not already present
        if "![" not in md_text and job.image_specs_json:
            section_matches = list(re.finditer(r"\n##\s+[^\n]+", md_text))
            step = max(1, len(section_matches) // (len(job.image_specs_json) + 1)) if section_matches else 1
            for i, spec in enumerate(job.image_specs_json):
                clean_name = spec.get("filename") or f"img_{i}.png"
                if not (images_dir / clean_name).exists():
                    continue
                caption = spec.get("caption", "")
                alt = spec.get("alt", "Technical Visual")
                img_tag = f"\n\n![{alt}](images/{clean_name})\n*{caption}*\n\n"
                if section_matches:
                    target_idx = min(len(section_matches) - 1, (i + 1) * step - 1)
                    pos = section_matches[target_idx].end()
                    next_p = md_text.find("\n\n", pos + 1)
                    insert_pos = next_p if next_p != -1 else pos
                    md_text = md_text[:insert_pos] + img_tag + md_text[insert_pos:]
                    section_matches = list(re.finditer(r"\n##\s+[^\n]+", md_text))
                else:
                    md_text += img_tag

        # Strip redundant leading H1 from body since it is already rendered in the publication header
        clean_md = re.sub(r"^\s*#\s+[^\n]+\n*", "", md_text, count=1)

        # Inline image files as base64 data URIs
        def replace_img(match):
            alt = match.group(1)
            raw_path = match.group(2)
            fname = Path(raw_path).name
            target_file = images_dir / fname
            if target_file.exists():
                b64 = base64.b64encode(target_file.read_bytes()).decode("utf-8")
                mime = "image/png"
                if fname.lower().endswith((".jpg", ".jpeg")):
                    mime = "image/jpeg"
                elif fname.lower().endswith(".svg"):
                    mime = "image/svg+xml"
                return f"![{alt}](data:{mime};base64,{b64})"
            return match.group(0)

        clean_md = re.sub(r"!\[([^\]]*)\]\((?:(?:images|\./images)/)?([^)]+)\)", replace_img, clean_md)

        # Numbered Citation conventions: map URLs and Source links to [1], [2], [3]
        evidence_items = list(job.evidence_json or [])
        url_to_idx = {}
        for idx, item in enumerate(evidence_items, start=1):
            url = item.get("url", "").strip() if isinstance(item, dict) else ""
            if url:
                url_to_idx[url] = idx

        def replace_citation(match):
            text = match.group(1)
            url = match.group(2).strip()
            if url in url_to_idx:
                return f"<sup>[{url_to_idx[url]}]</sup>"
            if text.lower() == "source":
                for u, idx in url_to_idx.items():
                    if u in url or url in u:
                        return f"<sup>[{idx}]</sup>"
                new_idx = len(evidence_items) + 1
                url_to_idx[url] = new_idx
                evidence_items.append({"title": url, "url": url})
                return f"<sup>[{new_idx}]</sup>"
            return match.group(0)

        clean_md = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", replace_citation, clean_md)

        # Also replace generic standalone "(Source)" strings with sequential reference numbers
        source_counter = [1]
        def replace_standalone_source(m):
            if evidence_items:
                c = source_counter[0]
                idx = min(c, len(evidence_items))
                source_counter[0] += 1
                return f"<sup>[{idx}]</sup>"
            return ""

        clean_md = re.sub(r"\(\s*Source\s*\)", replace_standalone_source, clean_md, flags=re.IGNORECASE)

        body_html = markdown.markdown(
            clean_md,
            extensions=["tables", "fenced_code", "nl2br", "attr_list"]
        )

        template_dir = Path(__file__).resolve().parent.parent.parent / "templates" / "pdf"
        jinja_env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=False)
        css_styles = ""
        styles_file = template_dir / "styles.css"
        if styles_file.exists():
            css_styles = styles_file.read_text(encoding="utf-8")
            # Strip @page:first from styles.css so it never zeroes out page 1 margins
            css_styles = re.sub(r"@page:first\s*\{[^}]*\}", "", css_styles, flags=re.DOTALL)

        template = jinja_env.get_template("research.html")
        html_content = template.render(
            title=blog_title,
            topic=job.topic,
            as_of=job.as_of,
            body_html=body_html,
            evidence_items=evidence_items,
            css_styles=css_styles
        )

        try:
            renderer = PlaywrightPDFRenderer()
            pdf_bytes = await renderer.render_html_to_pdf(html_content)
            cached_pdf.write_bytes(pdf_bytes)

            # Upload to MinIO object storage
            try:
                from app.integrations.storage.minio_client import storage_service
                minio_pdf_url = storage_service.upload_bytes(
                    pdf_bytes,
                    f"research/{job_id}/{pdf_filename}",
                    content_type="application/pdf"
                )
                self.repo.update_urls(job_id, pdf_url=minio_pdf_url)
            except Exception as up_err:
                logger.warning(f"MinIO PDF upload warning: {up_err}")

            return pdf_bytes, pdf_filename
        except Exception as e:
            logger.error(f"Playwright PDF rendering note ({e}). Falling back to reportlab.")
            from app.integrations.pdf.reportlab_renderer import ReportLabFallbackRenderer
            fallback_bytes = ReportLabFallbackRenderer().render_basic_pdf(
                title=blog_title,
                body=job.final_markdown
            )
            cached_pdf.write_bytes(fallback_bytes)

            try:
                from app.integrations.storage.minio_client import storage_service
                minio_pdf_url = storage_service.upload_bytes(
                    fallback_bytes,
                    f"research/{job_id}/{pdf_filename}",
                    content_type="application/pdf"
                )
                self.repo.update_urls(job_id, pdf_url=minio_pdf_url)
            except Exception as up_err:
                logger.warning(f"MinIO fallback PDF upload warning: {up_err}")

            return fallback_bytes, pdf_filename
