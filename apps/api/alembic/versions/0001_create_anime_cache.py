"""create anime_cache table

Revision ID: 0001
Revises:
Create Date: 2026-04-26

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "anime_cache",
        sa.Column("anilist_id", sa.Integer(), nullable=False),
        sa.Column("season", sa.String(length=10), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("genres", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("synopsis", sa.String(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("episodes", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("anilist_id", "season", "year"),
    )


def downgrade() -> None:
    op.drop_table("anime_cache")
