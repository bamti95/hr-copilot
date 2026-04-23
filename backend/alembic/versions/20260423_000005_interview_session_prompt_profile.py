"""interview session prompt profile

Revision ID: 20260423_000005
Revises: 2a64051356bf
Create Date: 2026-04-23 12:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260423_000005"
down_revision = "2a64051356bf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "interview_sessions",
        sa.Column("prompt_profile_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_interview_sessions_prompt_profile_id",
        "interview_sessions",
        "prompt_profile",
        ["prompt_profile_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_interview_sessions_prompt_profile_id",
        "interview_sessions",
        type_="foreignkey",
    )
    op.drop_column("interview_sessions", "prompt_profile_id")
