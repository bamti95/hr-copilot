"""prompt_profile updated_at

Revision ID: 20260420_000003
Revises: 20260417_000002
Create Date: 2026-04-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260420_000003"
down_revision = "20260417_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "prompt_profile",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(sa.text("UPDATE prompt_profile SET updated_at = created_at WHERE updated_at IS NULL"))
    op.alter_column("prompt_profile", "updated_at", nullable=False)


def downgrade() -> None:
    op.drop_column("prompt_profile", "updated_at")
