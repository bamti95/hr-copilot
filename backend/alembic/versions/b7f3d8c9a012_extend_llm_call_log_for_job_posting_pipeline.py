"""extend llm_call_log for job posting pipeline

Revision ID: b7f3d8c9a012
Revises: 63349b0a806d
Create Date: 2026-05-12 17:35:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b7f3d8c9a012"
down_revision = "63349b0a806d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "llm_call_log",
        "candidate_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.alter_column(
        "llm_call_log",
        "interview_sessions_id",
        existing_type=sa.Integer(),
        nullable=True,
    )

    op.add_column(
        "llm_call_log",
        sa.Column(
            "pipeline_type",
            sa.String(length=50),
            server_default="INTERVIEW_QUESTION",
            nullable=False,
        ),
    )
    op.add_column(
        "llm_call_log",
        sa.Column("target_type", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "llm_call_log",
        sa.Column("target_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "llm_call_log",
        sa.Column("job_posting_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "llm_call_log",
        sa.Column("job_posting_analysis_report_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "llm_call_log",
        sa.Column("knowledge_source_id", sa.Integer(), nullable=True),
    )

    op.create_foreign_key(
        "fk_llm_call_log_job_posting",
        "llm_call_log",
        "job_posting",
        ["job_posting_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_llm_call_log_job_posting_analysis_report",
        "llm_call_log",
        "job_posting_analysis_report",
        ["job_posting_analysis_report_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_llm_call_log_job_posting_knowledge_source",
        "llm_call_log",
        "job_posting_knowledge_source",
        ["knowledge_source_id"],
        ["id"],
    )

    op.create_index(
        "idx_llm_call_log_pipeline_type",
        "llm_call_log",
        ["pipeline_type"],
        unique=False,
    )
    op.create_index(
        "idx_llm_call_log_target",
        "llm_call_log",
        ["target_type", "target_id"],
        unique=False,
    )
    op.create_index(
        "idx_llm_call_log_job_posting_id",
        "llm_call_log",
        ["job_posting_id"],
        unique=False,
    )
    op.create_index(
        "idx_llm_call_log_job_posting_analysis_report_id",
        "llm_call_log",
        ["job_posting_analysis_report_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_llm_call_log_job_posting_analysis_report_id", table_name="llm_call_log")
    op.drop_index("idx_llm_call_log_job_posting_id", table_name="llm_call_log")
    op.drop_index("idx_llm_call_log_target", table_name="llm_call_log")
    op.drop_index("idx_llm_call_log_pipeline_type", table_name="llm_call_log")

    op.drop_constraint(
        "fk_llm_call_log_job_posting_knowledge_source",
        "llm_call_log",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_llm_call_log_job_posting_analysis_report",
        "llm_call_log",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_llm_call_log_job_posting",
        "llm_call_log",
        type_="foreignkey",
    )

    op.drop_column("llm_call_log", "knowledge_source_id")
    op.drop_column("llm_call_log", "job_posting_analysis_report_id")
    op.drop_column("llm_call_log", "job_posting_id")
    op.drop_column("llm_call_log", "target_id")
    op.drop_column("llm_call_log", "target_type")
    op.drop_column("llm_call_log", "pipeline_type")

    op.alter_column(
        "llm_call_log",
        "interview_sessions_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "llm_call_log",
        "candidate_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
