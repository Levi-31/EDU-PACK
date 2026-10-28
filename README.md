# Playlist Scholar — Agentic YouTube-to-Technical-Notes Platform

> Turn any YouTube playlist into an in-depth, publication-grade technical study guide and downloadable PDF with verified timestamp links and architectural diagrams.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2+-purple.svg)](https://langchain-ai.github.io/langgraph/)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB.svg)](https://react.dev/)
[![Playwright](https://img.shields.io/badge/Playwright-Chromium-green.svg)](https://playwright.dev/)

---

## 1. Overview & Capabilities

Playlist Scholar is an autonomous agentic platform engineered for learners, engineers, and researchers. It transforms multi-video YouTube playlists into dense, structured technical notes rather than shallow summaries.

### Key Capabilities
- **Strict Playlist Sequence Preservation**: Full pagination support for large playlists. Videos are processed with bounded concurrency but always preserved in their exact original sequence.
- **Grounded Transcripts & Verified Timestamps**: All note sections cite source transcript segment IDs. Video watch links include real timestamp parameters (`https://www.youtube.com/watch?v=VIDEO_ID&t=212s`). Zero invented timestamps.
- **LangGraph Multi-Agent Architecture**:
  1. *Coordinator Agent*: Plans execution and maintains stateful progress.
  2. *Transcript Processing Agent*: Handles semantic chunking, completeness checks, and quality validation.
  3. *Technical Notes Agent*: Generates executive summaries, learning objectives, detailed topics, callouts, and code blocks.
  4. *Visual / Diagram Agent*: Generates Mermaid architecture and sequence diagrams when pedagogically justified.
  5. *Notes Review / Critic Agent*: Rigorous fact-checking against transcript truth, enforcing bounded revisions.
- **Publication-Grade PDF Compilation**: Rendered via headless Chromium (Playwright). Features an editorial cover, clickable table of contents, video chapters, code blocks, diagrams, and a consolidated capstone revision guide.
- **Resilient Execution & Partial Success**: Private or caption-disabled videos are gracefully handled and transparently disclosed without crashing the remaining playlist.
- **Built-in Demo & Mock Mode**: Fully operational out-of-the-box without requiring live YouTube or OpenAI API keys.

---

## 2. Architecture & Tech Stack

```text
playlist-scholar/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application entrypoint
│   │   ├── api/v1/                  # HTTP controllers (playlists, jobs, notes, artifacts)
│   │   ├── core/                    # Settings, logging, custom exceptions
│   │   ├── domain/                  # Pydantic schemas and enums
│   │   ├── db/                      # SQLAlchemy models and repositories
│   │   ├── services/                # Application services (playlist, job, notes, pdf)
│   │   ├── integrations/            # Providers (YouTube, Transcripts, OpenAI, PDF, Storage)
│   │   ├── agents/                  # LangGraph workflow, state, prompts, specialist agents
│   │   ├── workers/                 # Celery & inline asyncio event bus
│   │   └── templates/pdf/           # Jinja2 templates & print CSS
│   ├── alembic/                     # Database migrations
│   └── tests/                       # Unit, integration, and E2E test suites
├── frontend/
│   ├── src/                         # React 18 + TypeScript + Tailwind CSS SPA
│   └── vite.config.ts               # Vite configuration with backend proxy
├── storage/                         # Local artifact storage (artifacts, visuals, uploads)
└── docker-compose.yml               # Production container orchestration
```

### Technology Highlights
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, Celery, Redis, LangGraph, Playwright Chromium, Jinja2.
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide React, TanStack Query, Server-Sent Events (SSE).
- **Persistence**: SQLite (local standalone) / PostgreSQL (production docker).

---

## 3. Quick Start (Local Development)

### Prerequisites
- Python 3.11 or newer
- Node.js 20+ & npm
- (Optional) Docker & Docker Compose

### Step 1: Clone and Configure Environment
```bash
git clone <repository-url>
cd playlist-scholar

# Copy environment configuration
cp .env.example .env
```

Review `.env`:
- By default, `DEMO_MODE=true` allows full interactive testing without any API credentials.
- To use live integrations, set `DEMO_MODE=false`, `YOUTUBE_API_KEY=your_key`, and `OPENAI_API_KEY=your_key`.

---

### Step 2: Set Up Backend

```bash
# Create and activate virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install backend dependencies
cd backend
pip install -e .
playwright install chromium

# Run database migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The API is live at `http://localhost:8000`. OpenAPI docs are accessible at `http://localhost:8000/docs`.

---

### Step 3: Set Up Frontend

In a separate terminal:
```bash
cd frontend

# Install npm dependencies
npm install

# Start Vite dev server
npm run dev
```
Open your browser at `http://localhost:3000`.

---

## 4. Running with Docker Compose

To run the complete production stack (PostgreSQL, Redis, FastAPI, Celery worker, and Nginx frontend):

```bash
docker-compose up --build
```
Access the application at `http://localhost:3000`.

---

## 5. Automated Testing

Playlist Scholar includes comprehensive unit tests, integration tests, and critical regression test suites.

```bash
# From workspace root
PYTHONPATH=backend .venv/bin/pytest backend/tests -v
```

### Critical Regressions Verified:
1. **Multi-page YouTube API pagination**: Handled cleanly across boundary pages.
2. **Strict Ordering Preservation**: Videos processed concurrently maintain original playlist position in storage, notes viewer, and PDF.
3. **Missing Transcripts Grounding**: Inaccessible videos disclose reason and do *not* fabricate notes.
4. **Resilience**: A failed or private video never blocks remaining playlist items.
5. **Verified Timestamps**: Links use genuine transcript start seconds (`?t=XXs`).
6. **Artifact Verification**: Output PDFs are verified for size, checksum, and chapter structure.

---

## 6. PDF Storage & Downloads

- Generated study guide PDFs are stored locally in `storage/artifacts/<job_id>/` and tracked via the `ArtifactRepository`.
- Files can be downloaded via the web interface or programmatically via:
  ```bash
  curl -O http://localhost:8000/api/v1/jobs/<job_id>/download
  ```

---

## 7. Known Limitations

- **Captions Disabled**: If a YouTube creator has disabled automatic and manual captions on a video and no user transcript is uploaded, that video chapter will state that captions were disabled rather than fabricating notes.
- **YouTube Rate Limits**: Production deployments processing heavy volume should monitor Google Cloud YouTube Data API quota.

---

## 8. License

MIT License. Designed with care for high-impact technical learning.
