from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.audit_base import AuditBase
from models.base import Base


class InterviewSession(Base, AuditBase):
    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidate.id"), nullable=False)
    target_job: Mapped[str] = mapped_column(String(50), nullable=False)
    difficulty_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    prompt_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("prompt_profile.id"),
        nullable=True,
    )
    question_generation_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="NOT_REQUESTED",
        server_default="NOT_REQUESTED",
    )
    question_generation_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    question_generation_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    question_generation_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    question_generation_progress: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )
