"""Add user_quota table for per-user Groq token spend tracking (v5.0.0 A5 Launch MVP).

Revision ID: 0018
Revises: 0017
Create Date: 2026-05-19
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DEFAULT_DAILY_LIMIT = 100_000


def upgrade() -> None:
    op.create_table(
        "user_quota",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("tokens_used_today", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("tokens_used_total", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("daily_limit", sa.Integer(), nullable=False, server_default=str(_DEFAULT_DAILY_LIMIT)),
        sa.Column("quota_reset_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_user_quota_user_id", "user_quota", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_quota_user_id", "user_quota")
    op.drop_table("user_quota")
