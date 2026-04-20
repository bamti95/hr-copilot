from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.audit_base import AuditBase
from models.base import Base


class PromptProfile(Base, AuditBase):
    __tablename__ = "prompt_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    output_schema: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
