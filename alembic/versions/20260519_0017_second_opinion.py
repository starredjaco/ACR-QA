"""Add findings.second_opinion_* columns for the Second Opinion engine (v5.0.0 A5).

Revision ID: 0017
Revises: 0016
Create Date: 2026-05-19
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("findings", sa.Column("second_opinion_primary_verdict", sa.String(16), nullable=True))
    op.add_column("findings", sa.Column("second_opinion_secondary_verdict", sa.String(16), nullable=True))
    op.add_column("findings", sa.Column("second_opinion_agreement", sa.Boolean(), nullable=True))
    op.add_column("findings", sa.Column("second_opinion_confidence_delta", sa.Integer(), nullable=True))
    op.add_column("findings", sa.Column("second_opinion_skipped", sa.String(64), nullable=True))


def downgrade() -> None:
    op.drop_column("findings", "second_opinion_skipped")
    op.drop_column("findings", "second_opinion_confidence_delta")
    op.drop_column("findings", "second_opinion_agreement")
    op.drop_column("findings", "second_opinion_secondary_verdict")
    op.drop_column("findings", "second_opinion_primary_verdict")
