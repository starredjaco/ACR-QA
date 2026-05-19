"""Add pr_risk_scores cache table (v5.0.0 A5 — PR Risk Score).

Revision ID: 0016
Revises: 0015
Create Date: 2026-05-19
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pr_risk_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "run_id",
            sa.Integer(),
            sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("band", sa.String(8), nullable=False),
        sa.Column("high_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reachable_high_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("exploit_verified_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("taint_path_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("changed_lines", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("file_risk_avg", sa.Float(), nullable=False, server_default="0"),
        sa.Column("contributions_json", sa.JSON(), nullable=True),
        sa.Column("explainer_json", sa.JSON(), nullable=True),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("pr_risk_scores")
