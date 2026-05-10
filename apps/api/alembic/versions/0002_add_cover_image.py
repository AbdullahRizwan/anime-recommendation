"""add cover_image to anime_cache

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-10

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("anime_cache", sa.Column("cover_image", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("anime_cache", "cover_image")
