# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

**tokens.to.systems** turns YouTube videos or playlists into technical study-guide PDFs (the "notes" subsystem), and turns a topic query into a researched article PDF (the "research" subsystem). The backend uses FastAPI, LangGraph and Celery, the frontend uses React, Vite and Tailwind, and PDFs are rendered with Playwright Chromium.

Internal identifiers still use the old names and are intentionally not renamed: `playlist_scholar` (DB, containers, package names), `PlaylistScholarException`, and the `synthara-storage` MinIO bucket. Only user-facing branding is "tokens.to.systems".

## Running it

The normal dev setup is the Docker stack (`docker-compose up --build`). The app is at http://localhost:3000, the API at :8000 (`/docs`), and the MinIO console at :9001.

These details are easy to get wrong:
- `backend/app` is bind-mounted into the backend and worker containers, but **neither uvicorn nor Celery auto-reloads**. After Python changes, run `docker restart playlist_scholar_backend playlist_scholar_worker`. Jinja templates under `backend/app/templates/pdf/` are read on each render, so they need no restart.
- The nginx frontend container serves the **bind-mounted `frontend/dist`**, not a dev server. After frontend changes, run `cd frontend && npm run build`, then hard-refresh the browser.
- Wipe all DB rows and the local `storage/artifacts` for a clean test with `docker exec playlist_scholar_backend python -m app.scripts.clear_data`. This does not touch the MinIO bucket.

Outside Docker, `JOB_RUNNER=inline` (the default) runs jobs in-process with no Redis or Celery, the DB defaults to SQLite at `storage/app.db`, and `DEMO_MODE=true` (the default) swaps in mock YouTube, transcript, OpenAI and Tavily clients so no API keys are needed.

## Tests

Run these from the repo root, using the root `.venv`:

```bash
PYTHONPATH=backend .venv/bin/pytest backend/tests/unit -q
PYTHONPATH=backend .venv/bin/pytest backend/tests/unit/test_research_layout_and_placement.py::test_name -q
PYTHONPATH=backend .venv/bin/pytest backend/tests/integration/test_pdf_figure_gaps.py -q   # needs local Playwright Chromium
```

`asyncio_mode = "auto"` is set in `backend/pyproject.toml`, and the `test_db` fixture is in-memory SQLite. `tests/integration/test_pdf_vector_diagrams.py` already fails with "no such table: artifacts", independent of current work.

There is no linter or formatter configured. For the frontend, `npm run build` (`tsc && vite build`) is the type check.

**Avoid paid runs.** A real research or notes job makes OpenAI, Tavily and image-generation calls that cost money. Verify PDF and layout changes offline instead: re-render an existing job's stored markdown through `research_service.get_pdf_file`, or call the download route.

## Architecture

### Job flow
API routers (`app/api/v1/`) → services (`app/services/`, `app/modules/research/research_service.py`) → `JobService` dispatches either inline or to Celery (`app/workers/celery_app.py`, which has the `execute_playlist_job` and `execute_research_job` tasks and calls into `app/workers/tasks.py`). Progress goes through `workers/event_bus.py` and reaches the frontend as SSE (`frontend/src/hooks/useJobProgress.ts`).

### Notes subsystem (`app/agents/`)
`agents/graph.py` is a three-node LangGraph: plan → process all videos → compile and validate PDF. Each video passes through the transcript, topic-planner, research, notes, visual (Mermaid) and review agents, and the review step can loop back for bounded revisions. Video order must always match the playlist order. The PDF comes from `services/pdf_service.py` using `templates/pdf/base.html` (cover, toc, chapter, revision partials, `styles.css`).

### Research subsystem (`app/modules/research/`)
`graph.py`: router → (optional web `research`) → `orchestrator` (produces a `Plan` and fans out with `Send`) → parallel `worker`s write sections → `reducer` subgraph (`nodes/reducer.py`):
1. `merge_content` joins the sections.
2. `decide_images` has the LLM propose visual specs only. It must **not** re-type the document, and `md_with_placeholders` stays empty because re-typing used to corrupt punctuation.
3. `generate_and_place_images` places each visual deterministically after the first paragraph of its `section_heading`.

**Visuals.** Mermaid is preferred over AI images. Mermaid code is validated with the real `mermaid.parse` in headless Chromium (`services/mermaid.py`) and falls back to an AI image if it fails to parse. AI images (`services/image.py`) are regenerated when content touches the image edge, and are dropped after repeated clipping. The markdown stores ```` ```mermaid ```` fences, which become `.diagram-box > .mermaid-canvas` in the PDF (rendered with `app/static/js/mermaid.min.js`) and are rendered by `MermaidDiagram.tsx` in the frontend.

**Text cleanup.** `text_cleanup.py` (`repair_control_chars`, `strip_reference_notes`) runs at merge time and again at PDF render.

**PDF caching.** `research_service.get_pdf_file` returns the cached PDF as-is when it is larger than 350KB. Smaller PDFs re-render on every download. Artifacts are stored in MinIO, and the frontend History page links straight to the MinIO URL.

### PDF rendering (`app/integrations/pdf/`)
- `playwright_renderer.py` is the main path. It renders with `outline=True, tagged=True`, which produces bookmarks and must stay on.
- Before printing, it runs `figure_layout.CLOSE_FIGURE_GAPS_JS`. This simulates page breaks for research PDFs and shrinks figures or moves the following text up so figures don't leave large gaps.
- `renderer.py` holds shared helpers:
  - `strip_pdf_metadata` blanks the `/Info` fields with same-length whitespace so xref offsets stay valid.
  - `fit_heading` and `shorten_title` keep the PDF title on one line.
- Every page carries a faint watermark from `templates/pdf/watermark.html`. It is an SVG drawn as a single outlined path on purpose, so it isn't searchable text and Chromium doesn't drop it after page 1.
- `reportlab_renderer.py` is a fallback that is rarely used.

### Storage
Postgres (Alembic migrations in `backend/alembic`, applied on backend container start), Redis (Celery broker), MinIO (`integrations/storage/`), and the local cache at `storage/artifacts/<job_id>/`.
