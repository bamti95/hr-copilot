from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from models.audit_base import AuditBase
from models.base import Base


class Candidate(Base, AuditBase):
    __tablename__ = "candidate"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    apply_status: Mapped[str] = mapped_column(String(30), nullable=False, default="APPLIED")
