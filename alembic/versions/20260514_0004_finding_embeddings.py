"""Add finding_embeddings table for learned suppression (Feature 10).

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-14 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "finding_embeddings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("finding_id", sa.Integer(), sa.ForeignKey("findings.id", ondelete="CASCADE"), nullable=True),
        sa.Column("rule_id", sa.String(100), nullable=False),
        sa.Column("code_context", sa.Text(), nullable=True),
        sa.Column("embedding_json", sa.Text(), nullable=False),
        sa.Column("suppressed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_finding_embeddings_rule_id", "finding_embeddings", ["rule_id"])


def downgrade() -> None:
    op.drop_index("ix_finding_embeddings_rule_id", table_name="finding_embeddings")
    op.drop_table("finding_embeddings")
