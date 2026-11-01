"""add research_jobs table and source_type to playlist_jobs

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-10-31 11:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add source_type and video_id to playlist_jobs
    op.add_column(
        'playlist_jobs',
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='playlist')
    )
    op.add_column(
        'playlist_jobs',
        sa.Column('video_id', sa.String(length=50), nullable=True)
    )

    # 2. Create research_jobs table
    op.create_table(
        'research_jobs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('topic', sa.Text(), nullable=False),
        sa.Column('as_of', sa.String(length=50), nullable=False),
        sa.Column('mode', sa.String(length=50), nullable=False, server_default='closed_book'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='QUEUED'),
        sa.Column('current_stage', sa.String(length=100), nullable=False, server_default='Initialized'),
        sa.Column('progress_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('queries_json', sa.JSON(), nullable=True),
        sa.Column('evidence_json', sa.JSON(), nullable=True),
        sa.Column('plan_json', sa.JSON(), nullable=True),
        sa.Column('sections_json', sa.JSON(), nullable=True),
        sa.Column('image_specs_json', sa.JSON(), nullable=True),
        sa.Column('final_markdown', sa.Text(), nullable=True),
        sa.Column('markdown_filename', sa.String(length=255), nullable=True),
        sa.Column('bundle_filename', sa.String(length=255), nullable=True),
        sa.Column('images_dir_path', sa.String(length=500), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('logs_json', sa.JSON(), nullable=True),
        sa.Column('is_mock', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f('ix_research_jobs_status'), 'research_jobs', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_research_jobs_status'), table_name='research_jobs')
    op.drop_table('research_jobs')
    op.drop_column('playlist_jobs', 'video_id')
    op.drop_column('playlist_jobs', 'source_type')

