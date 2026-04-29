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
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidate.id"), nullable=False)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("document.id"), nullable=True)

    prompt_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("prompt_profile.id"),
        nullable=True,
    )
    interview_sessions_id: Mapped[int] = mapped_column(
        ForeignKey("interview_sessions.id"),
        nullable=False,
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
