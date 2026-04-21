"""prompt_profile target_job

Revision ID: 20260421_000004
Revises: 20260420_000003
Create Date: 2026-04-21
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260421_000004"
down_revision = "20260420_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "prompt_profile",
        sa.Column("target_job", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("prompt_profile", "target_job")
