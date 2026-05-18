"""Add finding_chat_messages table for AI Chat Sidebar (v5.0.0 Phase A.1).

Revision ID: 0012
Revises: 0011
Create Date: 2026-05-18
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "finding_chat_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "finding_id",
            sa.Integer(),
            sa.ForeignKey("findings.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("preset", sa.String(32), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("model_name", sa.String(64), nullable=True),
        sa.Column("tokens_in", sa.Integer(), nullable=True),
        sa.Column("tokens_out", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_finding_chat_finding_created",
        "finding_chat_messages",
        ["finding_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_finding_chat_finding_created", table_name="finding_chat_messages")
    op.drop_table("finding_chat_messages")
