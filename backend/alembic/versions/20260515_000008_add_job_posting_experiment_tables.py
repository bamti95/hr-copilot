"""add job posting experiment tables

Revision ID: 20260515_000008
Revises: b7f3d8c9a012
Create Date: 2026-05-15 18:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260515_000008"
down_revision = "b7f3d8c9a012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_posting_experiment_run",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("dataset_name", sa.String(length=100), nullable=False),
        sa.Column("dataset_version", sa.String(length=50), nullable=True),
        sa.Column("experiment_type", sa.String(length=50), server_default="RAG_EVAL", nullable=False),
        sa.Column("status", sa.String(length=30), server_default="QUEUED", nullable=False),
        sa.Column("total_cases", sa.Integer(), server_default="0", nullable=False),
        sa.Column("completed_cases", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_cases", sa.Integer(), server_default="0", nullable=False),
        sa.Column("retrieval_recall_at_5", sa.Float(), nullable=True),
        sa.Column("macro_f1", sa.Float(), nullable=True),
        sa.Column("high_risk_recall", sa.Float(), nullable=True),
        sa.Column("source_omission_rate", sa.Float(), nullable=True),
        sa.Column("avg_latency_ms", sa.Float(), nullable=True),
        sa.Column("config_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("summary_metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("result_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ai_job_id", sa.Integer(), nullable=True),
        sa.Column("requested_by", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["ai_job_id"], ["ai_job.id"]),
        sa.ForeignKeyConstraint(["requested_by"], ["manager.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "job_posting_experiment_case_result",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("experiment_run_id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.String(length=100), nullable=False),
        sa.Column("case_index", sa.Integer(), server_default="0", nullable=False),
        sa.Column("job_group", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="PENDING", nullable=False),
        sa.Column("expected_label", sa.String(length=30), nullable=True),
        sa.Column("predicted_label", sa.String(length=30), nullable=True),
        sa.Column("expected_risk_types", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("predicted_risk_types", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("retrieval_hit_at_5", sa.Boolean(), nullable=True),
        sa.Column("source_omitted", sa.Boolean(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("evaluation_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("report_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["experiment_run_id"], ["job_posting_experiment_run.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("experiment_run_id", "case_id", name="uq_job_posting_experiment_case"),
    )


def downgrade() -> None:
    op.drop_table("job_posting_experiment_case_result")
    op.drop_table("job_posting_experiment_run")
