"""Add taint analysis columns to findings table.

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("findings", sa.Column("taint_source", sa.Text(), nullable=True))
    op.add_column("findings", sa.Column("taint_path", sa.JSON(), nullable=True))
    op.add_column("findings", sa.Column("taint_confidence", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("findings", "taint_confidence")
    op.drop_column("findings", "taint_path")
    op.drop_column("findings", "taint_source")
