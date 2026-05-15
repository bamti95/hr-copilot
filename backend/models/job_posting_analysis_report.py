"""채용공고 분석 결과 리포트를 저장하는 모델이다."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.audit_base import AuditBase
from models.base import Base

if TYPE_CHECKING:
    from models.job_posting import JobPosting


class JobPostingAnalysisStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class JobPostingAnalysisType(StrEnum):
    FULL = "FULL"
    RISK_ONLY = "RISK_ONLY"
    COMPLIANCE_ONLY = "COMPLIANCE_ONLY"
    ATTRACTIVENESS_ONLY = "ATTRACTIVENESS_ONLY"


class JobPostingAnalysisReport(Base, AuditBase):
    """
    채용공고 AI 분석 리포트 테이블.

    특정 채용공고(job_posting)에 대해 실행된 분석 결과를 저장
    공고 구조 파싱 결과, 감지된 리스크, 매칭된 RAG 근거,
    법률/공정성 경고, 개선 제안, 최종 리포트 JSON을 관리
    같은 채용공고에 대해 여러 개의 분석 이력을 가짐
    """
    __tablename__ = "job_posting_analysis_report"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    job_posting_id: Mapped[int] = mapped_column(
        ForeignKey("job_posting.id"),
        nullable=False,
    )

    analysis_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=JobPostingAnalysisStatus.PENDING.value,
    )
    analysis_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=JobPostingAnalysisType.FULL.value,
    )
    analysis_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    risk_level: Mapped[str | None] = mapped_column(String(30), nullable=True)
    issue_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    violation_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    warning_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    confidence_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detected_issue_types: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    retrieval_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pipeline_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    parsed_sections: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    overall_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attractiveness_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    issue_summary: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    matched_evidence: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    compliance_warnings: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    improvement_suggestions: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    rewrite_examples: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    final_report: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    ai_job_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_job.id"),
        nullable=True,
    )
    requested_by: Mapped[int | None] = mapped_column(
        ForeignKey("manager.id"),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

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

    job_posting: Mapped["JobPosting"] = relationship(
        "JobPosting",
        back_populates="analysis_reports",
    )
