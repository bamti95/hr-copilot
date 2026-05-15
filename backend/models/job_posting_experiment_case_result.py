"""채용공고 실험의 케이스별 결과 모델.

한 실험 안에서 개별 공고가 어떻게 예측되었는지 저장한다.
정답 라벨, 예측 라벨, 위험 유형, 검색 성공 여부, 지연 시간까지 함께 남겨 후속 분석에 쓴다.
"""

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
    """실험 케이스 1건의 실행 결과를 저장한다.

    실험 요약 지표는 이 테이블의 누적 결과를 바탕으로 계산한다.
    문제 케이스를 다시 추적할 수 있도록 평가 payload와 리포트 payload도 함께 보관한다.
    """
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
