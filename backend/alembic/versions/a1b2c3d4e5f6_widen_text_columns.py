"""widen text columns for video description and system messages

Revision ID: a1b2c3d4e5f6
Revises: ded1ebf3854b
Create Date: 2026-10-30 18:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'ded1ebf3854b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. playlist_videos
    op.alter_column(
        'playlist_videos', 'description',
        existing_type=sa.String(length=4000),
        type_=sa.Text(),
        existing_nullable=True
    )
    op.alter_column(
        'playlist_videos', 'title',
        existing_type=sa.String(length=500),
        type_=sa.String(length=1000),
        existing_nullable=False
    )

    # 2. playlist_jobs
    op.alter_column(
        'playlist_jobs', 'playlist_title',
        existing_type=sa.String(length=255),
        type_=sa.String(length=1000),
        existing_nullable=False
    )
    op.alter_column(
        'playlist_jobs', 'error_summary',
        existing_type=sa.String(length=1000),
        type_=sa.Text(),
        existing_nullable=True
    )

    # 3. job_events
    op.alter_column(
        'job_events', 'message',
        existing_type=sa.String(length=1000),
        type_=sa.Text(),
        existing_nullable=False
    )

    # 4. transcripts
    op.alter_column(
        'transcripts', 'error_message',
        existing_type=sa.String(length=1000),
        type_=sa.Text(),
        existing_nullable=True
    )

    # 5. visual_assets
    op.alter_column(
        'visual_assets', 'description',
        existing_type=sa.String(length=1000),
        type_=sa.Text(),
        existing_nullable=False
    )
    op.alter_column(
        'visual_assets', 'decision_reason',
        existing_type=sa.String(length=500),
        type_=sa.Text(),
        existing_nullable=True
    )


def downgrade() -> None:
    pass

