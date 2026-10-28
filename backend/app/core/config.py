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
    OPENAI_IMAGE_MODEL: str = "dall-e-3"
    OPENAI_MAX_RETRIES: int = 3
    OPENAI_TIMEOUT_SECONDS: int = 60
    MAX_CONCURRENT_LLM_REQUESTS: int = 3
    ENABLE_IMAGE_GENERATION: bool = True

    # Demo / Mock Mode
    DEMO_MODE: bool = True

    # Storage
    STORAGE_BACKEND: str = "local"
    STORAGE_DIR: str = str(ROOT_DIR / "storage")

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
