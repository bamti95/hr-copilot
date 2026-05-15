"""LLM 호출 로그와 사용량 메타데이터를 저장하는 모델이다."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.audit_base import AuditBase
from models.base import Base

class LlmCallLog(Base, AuditBase):
    __tablename__ = "llm_call_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("manager.id"), nullable=True)
    candidate_id: Mapped[int | None] = mapped_column(ForeignKey("candidate.id"), nullable=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("document.id"), nullable=True)

    prompt_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("prompt_profile.id"),
        nullable=True,
    )
    interview_sessions_id: Mapped[int | None] = mapped_column(
        ForeignKey("interview_sessions.id"),
        nullable=True,
    )
    pipeline_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="INTERVIEW_QUESTION",
        server_default="INTERVIEW_QUESTION",
    )
    target_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    job_posting_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_posting.id"),
        nullable=True,
    )
    job_posting_analysis_report_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_posting_analysis_report.id"),
        nullable=True,
    )
    knowledge_source_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_posting_knowledge_source.id"),
        nullable=True,
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    node_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    response_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 6),
        nullable=False,
        default=Decimal("0"),
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    elapsed_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_amount: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    call_status: Mapped[str] = mapped_column(String(30), nullable=False, default="success")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    call_time: Mapped[int] = mapped_column(Integer, nullable=False)
    
        # LangSmith 연결
    run_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    parent_run_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # 노드 타입
    run_type: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # 실행 순서
    execution_order: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # input / output 분리
    request_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # 시간 추적
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(nullable=True)

