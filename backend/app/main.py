import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import PlaylistScholarException
from app.db.session import init_db
from app.api.v1.playlists import router as playlists_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.notes import router as notes_router
from app.api.v1.artifacts import router as artifacts_router
from app.api.v1.research import router as research_router


setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger("playlist_scholar")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database schema...")
    init_db()
    logger.info(f"{settings.PROJECT_NAME} started successfully (DEMO_MODE={settings.DEMO_MODE}, RUNNER={settings.JOB_RUNNER}).")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Agentic YouTube-to-Technical-Notes Platform with High-Fidelity PDF Generation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for modern React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(PlaylistScholarException)
async def handle_custom_exception(request: Request, exc: PlaylistScholarException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "details": exc.details}
    )


# Health Check
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "demo_mode": settings.DEMO_MODE,
        "job_runner": settings.JOB_RUNNER,
        "database": "sqlite" if settings.is_sqlite else "postgresql"
    }


# Include v1 Routers
api_v1_prefix = "/api/v1"
app.include_router(playlists_router, prefix=api_v1_prefix)
app.include_router(jobs_router, prefix=api_v1_prefix)
app.include_router(notes_router, prefix=api_v1_prefix)
app.include_router(artifacts_router, prefix=api_v1_prefix)
app.include_router(research_router, prefix=api_v1_prefix)

# YouTube aliases for clean dual-mode API surface
app.include_router(playlists_router, prefix=f"{api_v1_prefix}/youtube")
app.include_router(jobs_router, prefix=f"{api_v1_prefix}/youtube")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

