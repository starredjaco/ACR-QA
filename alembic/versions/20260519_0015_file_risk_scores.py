"""Add file_risk_scores cache table for the Heuristic Risk Predictor (v5.0.0 A3).

Revision ID: 0015
Revises: 0014
Create Date: 2026-05-19
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "file_risk_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "run_id",
            sa.Integer(),
            sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("file_path", sa.String(1024), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("complexity", sa.Float(), nullable=False, server_default="0"),
        sa.Column("churn_90d", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("age_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("author_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("test_coverage_gap", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("high_finding_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("loc", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("run_id", "file_path", name="ux_file_risk_run_path"),
    )
    op.create_index("ix_file_risk_run_score", "file_risk_scores", ["run_id", "score"])


def downgrade() -> None:
    op.drop_index("ix_file_risk_run_score", table_name="file_risk_scores")
    op.drop_table("file_risk_scores")
