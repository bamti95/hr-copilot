"""지원자 기본 정보와 상태를 저장하는 모델이다."""

from typing import TYPE_CHECKING

from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.audit_base import AuditBase
from models.base import Base

if TYPE_CHECKING:
    from models.document import Document

class ApplyStatus(StrEnum):
    APPLIED = "APPLIED"
    SCREENING = "SCREENING"
    INTERVIEW = "INTERVIEW"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    
class JobPosition(StrEnum):
    STRATEGY_PLANNING = "STRATEGY_PLANNING"   # 기획·전략
    HR = "HR"                                 # 인사·HR
    MARKETING = "MARKETING"                   # 마케팅·광고·MD
    AI_DEV_DATA = "AI_DEV_DATA"               # AI·개발·데이터
    SALES = "SALES"                           # 영업
    
class Candidate(Base, AuditBase):
    __tablename__ = "candidate"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    
    job_position: Mapped[str] = mapped_column(
        String(50),
        nullable=True
    )
    
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    apply_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=ApplyStatus.APPLIED.value
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="candidate",
    )
