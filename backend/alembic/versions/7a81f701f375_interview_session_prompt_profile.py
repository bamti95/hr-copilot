"""interview session prompt profile

Revision ID: 7a81f701f375
Revises: 20260423_000005
Create Date: 2026-04-23 11:39:48.796226
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7a81f701f375"
down_revision = "20260423_000005"
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
        "prompt_profile",  # 실제 테이블명이 prompt_profiles면 이 부분 수정
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