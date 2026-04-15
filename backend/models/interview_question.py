from sqlalchemy import ForeignKey, Integer, String, Text
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
    follow_up_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluation_guide: Mapped[str | None] = mapped_column(Text, nullable=True)
    question_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
