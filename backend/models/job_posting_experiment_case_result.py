from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.audit_base import AuditBase
from models.base import Base

if TYPE_CHECKING:
    from models.job_posting_experiment_run import JobPostingExperimentRun


class JobPostingExperimentCaseResult(Base, AuditBase):
    __tablename__ = "job_posting_experiment_case_result"
    __table_args__ = (
        UniqueConstraint("experiment_run_id", "case_id", name="uq_job_posting_experiment_case"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    experiment_run_id: Mapped[int] = mapped_column(
        ForeignKey("job_posting_experiment_run.id"),
        nullable=False,
    )
    case_id: Mapped[str] = mapped_column(String(100), nullable=False)
    case_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    job_group: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",
        server_default="PENDING",
    )

    expected_label: Mapped[str | None] = mapped_column(String(30), nullable=True)
    predicted_label: Mapped[str | None] = mapped_column(String(30), nullable=True)
    expected_risk_types: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    predicted_risk_types: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    retrieval_hit_at_5: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    source_omitted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluation_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    report_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    experiment_run: Mapped["JobPostingExperimentRun"] = relationship(
        "JobPostingExperimentRun",
        back_populates="case_results",
    )
