"""면접 세션에 속한 생성 질문을 저장하는 모델이다."""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.audit_base import AuditBase
from models.base import Base


class InterviewQuestion(Base, AuditBase):
    __tablename__ = "interview_question"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interview_sessions_id: Mapped[int] = mapped_column(
        ForeignKey("interview_sessions.id"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_answer_basis: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_basis: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluation_guide: Mapped[str | None] = mapped_column(Text, nullable=True)
    question_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_evidence: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    risk_tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    competency_tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    review_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    review_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_recommended_revision: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

