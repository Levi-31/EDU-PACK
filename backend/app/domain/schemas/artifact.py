from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.domain.enums import ArtifactType


class ArtifactSchema(BaseModel):
    id: str
    job_id: str
    artifact_type: ArtifactType
    file_name: str
    file_path: str
    mime_type: str
    file_size_bytes: int
    checksum_sha256: str
    created_at: datetime
    download_url: str
    file_url: Optional[str] = None
    is_valid: bool = True

