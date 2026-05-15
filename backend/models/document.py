"""지원자 업로드 문서 메타데이터와 추출 상태를 저장하는 모델이다."""

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.audit_base import AuditBase
from models.base import Base

if TYPE_CHECKING:
    from models.candidate import Candidate


class Document(Base, AuditBase):
    __tablename__ = "document"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    
    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_ext: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidate.id"), nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extract_status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    candidate: Mapped["Candidate"] = relationship(
        "Candidate",
        back_populates="documents",
    )

