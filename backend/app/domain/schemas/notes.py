from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from app.domain.schemas.visual import VisualAssetSchema


class CodeSnippet(BaseModel):
    language: str = Field(default="python", description="Language of code or 'bash', 'json', 'yaml', etc.")
    code: str = Field(description="Executable or illustrative snippet")
    caption: Optional[str] = Field(default=None, description="Optional caption explaining the code")


class CalloutBox(BaseModel):
    kind: str = Field(default="tip", description="'note', 'tip', 'important', 'warning', or 'caution'")
    title: str = Field(description="Callout title")
    content: str = Field(description="Markdown callout content")


class Flashcard(BaseModel):
    question: str = Field(description="Conceptual or practical question")
    answer: str = Field(description="Concise, accurate answer")


class GlossaryItem(BaseModel):
    term: str = Field(description="Technical term or acronym")
    definition: str = Field(description="Clear technical definition")


class NoteTopicSection(BaseModel):
    title: str = Field(description="Descriptive topic title")
    markdown_content: str = Field(description="In-depth conceptual and technical explanation in markdown")
    code_snippets: List[CodeSnippet] = Field(default_factory=list, description="Code snippets or terminal commands")
    callouts: List[CalloutBox] = Field(default_factory=list, description="Educational callout boxes")
    visual: Optional[VisualAssetSchema] = Field(default=None, description="Optional embedded diagram or visual asset")
    evidence_segment_ids: List[str] = Field(default_factory=list, description="Transcript segment IDs supporting this section")
    timestamp_seconds: Optional[float] = Field(default=None, description="Resolved start timestamp from evidence")
    timestamped_watch_url: Optional[str] = Field(default=None, description="Resolved YouTube watch URL with timestamp")


class ReviewReport(BaseModel):
    status: str = Field(default="APPROVED", description="APPROVED, REVISED, or FLAGGED")
    groundedness_score: float = Field(default=1.0, description="0.0 to 1.0 confidence that claims match transcript")
    findings: List[str] = Field(default_factory=list, description="Specific critique findings or verification points")
    revisions_applied: int = Field(default=0, description="Number of revision cycles applied")


class StructuredVideoNotes(BaseModel):
    schema_version: str = "1.0"
    video_id: str
    video_title: str
    video_url: str
    channel_name: Optional[str] = None
    duration_seconds: Optional[int] = None
    thumbnail_url: Optional[str] = None
    original_position: int = 0

    # Executive Summary & Objectives
    executive_summary: str = Field(description="One-paragraph dense technical summary of the video")
    key_takeaways: List[str] = Field(default_factory=list, description="3-5 bulleted high-impact takeaways")
    learning_objectives: List[str] = Field(default_factory=list, description="Concrete skills or concepts gained")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisite knowledge required")

    # In-Depth Content
    core_concepts: List[str] = Field(default_factory=list, description="Primary technical concepts covered")
    sections: List[NoteTopicSection] = Field(default_factory=list, description="Detailed topic sections in order")
    architecture_and_workflows: Optional[str] = Field(default=None, description="System architecture or process workflows")
    trade_offs_and_decisions: List[str] = Field(default_factory=list, description="Key design trade-offs and choices discussed")
    pitfalls_and_limitations: List[str] = Field(default_factory=list, description="Common mistakes, caveats, or anti-patterns")
    
    # Review & Revision Aids
    glossary: List[GlossaryItem] = Field(default_factory=list, description="Glossary of technical terms")
    revision_sheet: str = Field(description="Concise cheat sheet / quick-reference summary")
    flashcards: List[Flashcard] = Field(default_factory=list, description="Review questions or flashcards")

    # Provenance & Review
    transcript_language: str = "en"
    transcript_source: str = "youtube"
    is_mock: bool = False
    review_report: ReviewReport = Field(default_factory=ReviewReport)
