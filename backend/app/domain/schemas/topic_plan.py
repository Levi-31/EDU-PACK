from typing import List, Optional
from pydantic import BaseModel, Field


class PlannedTopic(BaseModel):
    topic_id: str = Field(description="Unique topic ID, e.g. topic_1")
    title: str = Field(description="Descriptive topic title")
    start_seconds: Optional[float] = Field(default=None, description="Start timestamp in video if identifiable")
    end_seconds: Optional[float] = Field(default=None, description="End timestamp in video if identifiable")
    summary: str = Field(description="Brief summary of what this topic covers")
    learning_objectives: List[str] = Field(default_factory=list, description="What the learner will master")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisite concepts needed")
    theoretical_depth_needed: str = Field(default="medium", description="high, medium, or introductory")
    research_queries: List[str] = Field(default_factory=list, description="0-2 specific search queries to retrieve foundational theory/RFCs")
    suggested_diagram_type: Optional[str] = Field(default=None, description="e.g. architecture, sequence, flowchart, stateDiagram, none")


class VideoTopicPlan(BaseModel):
    video_id: str
    video_title: str
    overall_subject: str = Field(description="Core discipline or technical domain")
    audience_level: str = Field(default="Intermediate", description="Beginner, Intermediate, or Advanced")
    planned_topics: List[PlannedTopic] = Field(default_factory=list, description="Decomposed sequence of topics")
    global_research_queries: List[str] = Field(default_factory=list, description="Broader searches for foundational documentation or standards")

