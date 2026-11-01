"""add minio storage url columns to research_jobs, playlist_jobs, and artifacts

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-11-01 00:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add MinIO URLs to research_jobs
    op.add_column('research_jobs', sa.Column('pdf_url', sa.String(length=1000), nullable=True))
    op.add_column('research_jobs', sa.Column('bundle_url', sa.String(length=1000), nullable=True))
    op.add_column('research_jobs', sa.Column('markdown_url', sa.String(length=1000), nullable=True))
    op.add_column('research_jobs', sa.Column('image_urls_json', sa.JSON(), nullable=True))

    # Add MinIO URL to playlist_jobs
    op.add_column('playlist_jobs', sa.Column('pdf_url', sa.String(length=1000), nullable=True))

    # Add MinIO URL to artifacts
    op.add_column('artifacts', sa.Column('file_url', sa.String(length=1000), nullable=True))


def downgrade() -> None:
    op.drop_column('artifacts', 'file_url')
    op.drop_column('playlist_jobs', 'pdf_url')
    op.drop_column('research_jobs', 'image_urls_json')
    op.drop_column('research_jobs', 'markdown_url')
    op.drop_column('research_jobs', 'bundle_url')
    op.drop_column('research_jobs', 'pdf_url')

