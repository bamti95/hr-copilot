"""async question generation state and results

Revision ID: 20260425_000006
Revises: 7a81f701f375
Create Date: 2026-04-25 12:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260425_000006"
down_revision = "7a81f701f375"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "interview_sessions",
        sa.Column(
            "question_generation_status",
            sa.String(length=20),
            server_default="NOT_REQUESTED",
            nullable=False,
        ),
    )
    op.add_column(
        "interview_sessions",
        sa.Column("question_generation_error", sa.Text(), nullable=True),
    )
    op.add_column(
        "interview_sessions",
        sa.Column(
            "question_generation_requested_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "interview_sessions",
        sa.Column(
            "question_generation_completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "interview_question",
        sa.Column("expected_answer_basis", sa.Text(), nullable=True),
    )
    op.add_column(
        "interview_question",
        sa.Column("follow_up_basis", sa.Text(), nullable=True),
    )
    op.add_column(
        "interview_question",
        sa.Column("document_evidence", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "interview_question",
        sa.Column("risk_tags", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "interview_question",
        sa.Column("competency_tags", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "interview_question",
        sa.Column("review_status", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "interview_question",
        sa.Column("review_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "interview_question",
        sa.Column("review_reject_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "interview_question",
        sa.Column("review_recommended_revision", sa.Text(), nullable=True),
    )
    op.add_column(
        "interview_question",
        sa.Column("score", sa.Integer(), nullable=True),
    )
    op.add_column(
        "interview_question",
        sa.Column("score_reason", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("interview_question", "score_reason")
    op.drop_column("interview_question", "score")
    op.drop_column("interview_question", "review_recommended_revision")
    op.drop_column("interview_question", "review_reject_reason")
    op.drop_column("interview_question", "review_reason")
    op.drop_column("interview_question", "review_status")
    op.drop_column("interview_question", "competency_tags")
    op.drop_column("interview_question", "risk_tags")
    op.drop_column("interview_question", "document_evidence")
    op.drop_column("interview_question", "follow_up_basis")
    op.drop_column("interview_question", "expected_answer_basis")

    op.drop_column("interview_sessions", "question_generation_completed_at")
    op.drop_column("interview_sessions", "question_generation_requested_at")
    op.drop_column("interview_sessions", "question_generation_error")
    op.drop_column("interview_sessions", "question_generation_status")
