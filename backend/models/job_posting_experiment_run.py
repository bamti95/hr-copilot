from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.audit_base import AuditBase
from models.base import Base

if TYPE_CHECKING:
    from models.job_posting_experiment_case_result import JobPostingExperimentCaseResult


class JobPostingExperimentStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class JobPostingExperimentRun(Base, AuditBase):
    __tablename__ = "job_posting_experiment_run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    dataset_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dataset_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    experiment_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="RAG_EVAL",
        server_default="RAG_EVAL",
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=JobPostingExperimentStatus.QUEUED.value,
        server_default=JobPostingExperimentStatus.QUEUED.value,
    )

    total_cases: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    completed_cases: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    failed_cases: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    retrieval_recall_at_5: Mapped[float | None] = mapped_column(Float, nullable=True)
    macro_f1: Mapped[float | None] = mapped_column(Float, nullable=True)
    high_risk_recall: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_omission_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    config_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    summary_metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    ai_job_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_job.id"),
        nullable=True,
    )
    requested_by: Mapped[int | None] = mapped_column(
        ForeignKey("manager.id"),
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    case_results: Mapped[list["JobPostingExperimentCaseResult"]] = relationship(
        "JobPostingExperimentCaseResult",
        back_populates="experiment_run",
        cascade="all, delete-orphan",
    )
