"""add manager id to llm call log

Revision ID: 20260429_000007
Revises: 20260425_000006
Create Date: 2026-04-29 17:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260429_000007"
down_revision = "20260425_000006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "llm_call_log",
        sa.Column("manager_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_llm_call_log_manager_id",
        "llm_call_log",
        "manager",
        ["manager_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_llm_call_log_manager_id",
        "llm_call_log",
        type_="foreignkey",
    )
    op.drop_column("llm_call_log", "manager_id")
