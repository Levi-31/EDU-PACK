from typing import Optional
from pydantic import BaseModel, Field
from app.domain.enums import VisualType


class VisualAssetSchema(BaseModel):
    id: Optional[str] = None
    video_id: str = Field(default="")
    section_index: Optional[int] = None
    asset_type: VisualType = Field(default=VisualType.MERMAID_FLOWCHART)
    title: str = Field(default="", description="Title or heading for the visual asset")
    description: str = Field(default="", description="Explanation or educational context of what the visual depicts")
    mermaid_code: Optional[str] = Field(default=None, description="Mermaid DSL code for diagrams")
    image_url: Optional[str] = Field(default=None, description="URL or relative path to rendered image/diagram asset")
    mime_type: str = "image/svg+xml"
    storage_key: Optional[str] = None
    is_generated: bool = False
    decision_reason: Optional[str] = Field(default=None, description="Why this visual was or was not justified")

