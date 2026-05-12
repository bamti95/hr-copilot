from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.audit_base import AuditBase
from models.base import Base

if TYPE_CHECKING:
    from models.job_posting_analysis_report import JobPostingAnalysisReport


class JobPostingInputSource(StrEnum):
    MANUAL = "MANUAL"
    SARAMIN_API = "SARAMIN_API"
    WORKNET_API = "WORKNET_API"
    WANTED_API = "WANTED_API"
    SYNTHETIC = "SYNTHETIC"


class JobPostingStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class JobPosting(Base, AuditBase):
    """
    채용공고 원본 테이블.

    HR 담당자가 직접 작성한 공고, 외부 채용 API에서 수집한 공고
    가상 테스트 공고의 원문과 기본 메타데이터를 저장
    하나의 채용공고는 여러 번 분석될 수 있다람쥐
    분석 결과는 job_posting_analysis_report 테이블에 별도로 저장
    """
    __tablename__ = "job_posting"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    input_source: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=JobPostingInputSource.MANUAL.value,
    )
    source_platform: Mapped[str | None] = mapped_column(String(50), nullable=True)
    external_posting_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    external_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    target_job: Mapped[str | None] = mapped_column(String(100), nullable=True)
    career_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    salary_text: Mapped[str | None] = mapped_column(String(255), nullable=True)

    posting_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    posting_text_hash: Mapped[str] = mapped_column(String(64), nullable=False) # 같은 공고 중복 분석 방지 hash

    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    normalized_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    posting_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=JobPostingStatus.DRAFT.value,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    analysis_reports: Mapped[list["JobPostingAnalysisReport"]] = relationship(
        "JobPostingAnalysisReport",
        back_populates="job_posting",
        cascade="all, delete-orphan",
    )