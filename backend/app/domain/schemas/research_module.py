from __future__ import annotations
from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class CreateResearchJobRequest(BaseModel):
    topic: str = Field(..., min_length=3, description="Technical topic to research and synthesize")
    as_of: Optional[str] = Field(default=None, description="As-of date in YYYY-MM-DD format (defaults to current date)")
    image_provider: Optional[Literal["gemini", "openai", "dall-e", "dalle"]] = Field(
        default=None,
        description="Image generation provider (gemini or openai)"
    )
    search_provider: Optional[Literal["tavily"]] = Field(
        default=None,
        description="Search provider for web evidence retrieval"
    )


class ResearchJobDetailResponse(BaseModel):
    id: str
    topic: str
    as_of: str
    mode: str = "closed_book"
    status: str = "QUEUED"
    current_stage: str = "Initialized"
    progress_percentage: float = 0.0

    plan: Optional[Dict[str, Any]] = None
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    image_specs: List[Dict[str, Any]] = Field(default_factory=list)
    sections: List[Any] = Field(default_factory=list)

    final_markdown: Optional[str] = None
    markdown_content: Optional[str] = None
    article_title: Optional[str] = None
    markdown_filename: Optional[str] = None
    bundle_filename: Optional[str] = None
    pdf_url: Optional[str] = None
    bundle_url: Optional[str] = None
    markdown_url: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    image_urls: List[str] = Field(default_factory=list)
    logs: List[str] = Field(default_factory=list)

    error_message: Optional[str] = None
    error_summary: Optional[str] = None
    is_mock: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None



class ResearchJobListResponse(BaseModel):
    jobs: List[ResearchJobDetailResponse]
    total: int
    page: int = 1
    page_size: int = 20
