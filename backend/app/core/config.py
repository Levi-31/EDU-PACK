from pathlib import Path
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BASE_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "Playlist Scholar"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "dev-insecure-secret-key-change-in-production"

    # Database
    DATABASE_URL: str = Field(default="sqlite:///./storage/app.db")

    # Background runner
    JOB_RUNNER: Literal["inline", "celery"] = "inline"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_CONCURRENCY: int = 4

    # YouTube API
    YOUTUBE_API_KEY: str = ""

    # OpenAI API
    OPENAI_API_KEY: str = ""
    OPENAI_TEXT_MODEL: str = "gpt-4o-mini"
    OPENAI_REVIEW_MODEL: str = "gpt-4o-mini"
    OPENAI_IMAGE_MODEL: str = "gpt-image-1-mini"
    OPENAI_MAX_RETRIES: int = 3
    OPENAI_TIMEOUT_SECONDS: int = 300
    MAX_CONCURRENT_LLM_REQUESTS: int = 3
    ENABLE_IMAGE_GENERATION: bool = True

    # Tavily Web Research
    TAVILY_API_KEY: str = ""
    ENABLE_WEB_RESEARCH: bool = True
    TAVILY_MAX_RESULTS: int = 5
    TAVILY_SEARCH_DEPTH: str = "advanced"
    RESEARCH_QUERIES_PER_VIDEO: int = 3
    MAX_RESEARCH_SOURCES_PER_TOPIC: int = 5
    MAX_PARALLEL_RESEARCH: int = 3
    RESEARCH_CACHE_TTL_HOURS: int = 24

    # Demo / Mock Mode
    DEMO_MODE: bool = True

    # Research Module Integration (Levi-31/Research-Tool)
    ENABLE_RESEARCH_MODULE: bool = True
    RESEARCH_OPENAI_MODEL: str = "gpt-4o-mini"
    SEARCH_PROVIDER: str = "tavily"
    IMAGE_PROVIDER: str = "openai"
    GOOGLE_API_KEY: str = ""
    RESEARCH_AS_OF_DATE: str = ""

    # Storage
    STORAGE_BACKEND: str = "minio"
    STORAGE_DIR: str = str(ROOT_DIR / "storage")

    # MinIO Object Storage
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ROOT_USER: str = "minioadmin"
    MINIO_ROOT_PASSWORD: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "synthara-storage"
    MINIO_PUBLIC_URL: str = "http://localhost:9000"
    MINIO_SECURE: bool = False

    # PDF Renderer
    PDF_RENDERER: Literal["playwright", "reportlab"] = "playwright"

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def normalized_database_url(self) -> str:
        if self.DATABASE_URL.startswith("sqlite:///./"):
            rel_path = self.DATABASE_URL.replace("sqlite:///./", "")
            abs_path = (ROOT_DIR / rel_path).resolve()
            return f"sqlite:///{abs_path}"
        return self.DATABASE_URL

    @property
    def storage_path(self) -> Path:
        p = Path(self.STORAGE_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def artifacts_path(self) -> Path:
        p = self.storage_path / "artifacts"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def visuals_path(self) -> Path:
        p = self.storage_path / "visuals"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def uploads_path(self) -> Path:
        p = self.storage_path / "uploads"
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
