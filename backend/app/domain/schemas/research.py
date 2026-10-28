from typing import List, Optional
from pydantic import BaseModel, Field


class ResearchSource(BaseModel):
    title: str = Field(description="Title of documentation, article, or specification")
    url: str = Field(description="Authoritative reference URL")
    domain: str = Field(default="", description="Source domain, e.g. cloud.google.com, rfc-editor.org")
    snippet: str = Field(description="Relevant technical excerpt or summary")
    relevance_summary: Optional[str] = Field(default=None, description="Why this source informs the notes")
    score: Optional[float] = Field(default=None, description="Search relevance score")


class TopicResearchResult(BaseModel):
    topic_id: str
    query: str
    sources: List[ResearchSource] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)


class VideoResearchBundle(BaseModel):
    video_id: str
    queries_executed: List[str] = Field(default_factory=list)
    sources: List[ResearchSource] = Field(default_factory=list)
    topic_results: List[TopicResearchResult] = Field(default_factory=list)
    enrichment_notes: Optional[str] = Field(default=None, description="Synthesized summary of theoretical insights")

