# Playlist Scholar — Architecture & System Design

## 1. High-Level Architecture Overview

Playlist Scholar transforms multi-video YouTube playlists into dense, production-grade technical learning notes and publication-ready study guide PDFs.

```mermaid
flowchart TD
    User([User / Browser]) <--> ReactUI[Vite React Frontend]
    ReactUI <-->|HTTP REST & SSE| FastAPIServer[FastAPI Server v1]
    
    subgraph Core Platform
        FastAPIServer --> JobService[Job & Playlist Service]
        JobService --> Repositories[SQLAlchemy Repositories]
        Repositories <--> SQLite_PG[(PostgreSQL / SQLite DB)]
        JobService --> EventBus[Async Event Bus / SSE]
    end

    subgraph Agentic Orchestration Layer - LangGraph
        JobService --> Coordinator[Coordinator / Planner Agent]
        Coordinator --> TranscriptAgent[Transcript Processing Agent]
        TranscriptAgent --> NotesAgent[Technical Notes Agent - OpenAI]
        NotesAgent --> VisualAgent[Visual & Diagram Agent - Mermaid]
        VisualAgent --> ReviewAgent[Critic / Fact-Checking Agent]
        ReviewAgent --> Compiler[PDF Compilation Service]
    end

    subgraph Output & Storage
        Compiler --> PlaywrightEngine[Playwright Chromium Renderer]
        PlaywrightEngine --> PDFStorage[(Local / S3 Storage)]
        PDFStorage --> DownloadEndpoint[/api/v1/jobs/{id}/download]
    end
```

---

## 2. Layered Component Responsibilities

### A. Controller / API Layer (`backend/app/api/`)
- Pure HTTP interface validating payloads and exposing OpenAPI contracts.
- Routes:
  - `POST /api/v1/playlists/preview`
  - `POST /api/v1/jobs`
  - `GET /api/v1/jobs`
  - `GET /api/v1/jobs/{job_id}`
  - `GET /api/v1/jobs/{job_id}/events` (Server-Sent Events)
  - `POST /api/v1/jobs/{job_id}/retry`
  - `POST /api/v1/jobs/{job_id}/cancel`
  - `GET /api/v1/jobs/{job_id}/notes`
  - `GET /api/v1/jobs/{job_id}/download`

### B. Application Service Layer (`backend/app/services/`)
- Encapsulates business logic, transactional operations, and service coordination.
- `PlaylistService`: Validates playlist links and extracts ordered videos.
- `JobService`: Manages job queues, idempotency, retry loops, and progress reporting.
- `NotesService`: Retrieves structured note representations.
- `PDFService`: Compiles Jinja2 templates into HTML and drives Playwright PDF generation.

### C. Repository Layer (`backend/app/db/repositories/`)
- Isolated data persistence abstractions preventing direct queries in route handlers.
- `PlaylistJobRepository`, `PlaylistVideoRepository`, `TranscriptRepository`, `NotesRepository`, `ArtifactRepository`, `EventRepository`.

### D. Agentic Orchestration Layer (`backend/app/agents/`)
- Orchestrated with LangGraph state graphs with strict type definitions:
  - **Coordinator**: Formulates execution plan and sets progress bounds.
  - **Transcript Agent**: Normalizes text, validates completeness, chunks long transcripts, and preserves evidence segment IDs.
  - **Technical Notes Agent**: Synthesizes structured markdown, key takeaways, code blocks, and resolves segment IDs to verified video timestamps (`?t=XXs`).
  - **Visual Agent**: Conditionally generates Mermaid diagrams (flowcharts, sequence, architecture).
  - **Review/Critic Agent**: Verifies factual grounding against transcript, checks for hallucinations, and triggers bounded revisions.

### E. PDF Generation & Artifact Validation (`backend/app/integrations/pdf/`)
- Built using Jinja2 templates (`cover.html`, `toc.html`, `chapter.html`, `revision.html`) and print CSS.
- Rendered with Playwright headless Chromium for pixel-perfect printing and clickable external/internal links.
- Artifact verification confirms file existence, size, SHA256 checksum, and chapter ordering.
