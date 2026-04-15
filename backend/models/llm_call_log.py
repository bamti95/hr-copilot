from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.audit_base import AuditBase
from models.base import Base


class LlmCallLog(Base, AuditBase):
    __tablename__ = "llm_call_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidate.id"), nullable=False)
    document_id: Mapped[int] = mapped_column(ForeignKey("document.id"), nullable=False)
    prompt_profile_id: Mapped[int] = mapped_column(ForeignKey("prompt_profile.id"), nullable=False)
    interview_sessions_id: Mapped[int] = mapped_column(
        ForeignKey("interview_sessions.id"),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    response_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_amount: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    call_status: Mapped[str] = mapped_column(String(20), nullable=False)
    call_time: Mapped[int] = mapped_column(Integer, nullable=False)
