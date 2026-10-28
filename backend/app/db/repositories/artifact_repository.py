from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.artifact import Artifact
from app.db.repositories.base import BaseRepository


class ArtifactRepository(BaseRepository[Artifact]):
    def __init__(self, db: Session):
        super().__init__(Artifact, db)

    def get_by_job_id(self, job_id: str, artifact_type: str = "pdf_notes") -> Optional[Artifact]:
        return (
            self.db.query(Artifact)
            .filter(Artifact.job_id == job_id, Artifact.artifact_type == artifact_type)
            .order_by(Artifact.created_at.desc())
            .first()
        )

    def list_by_job_id(self, job_id: str) -> List[Artifact]:
        return (
            self.db.query(Artifact)
            .filter(Artifact.job_id == job_id)
            .order_by(Artifact.created_at.desc())
            .all()
        )

