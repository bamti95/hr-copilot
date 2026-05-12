from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.audit_base import AuditBase
from models.base import Base

if TYPE_CHECKING:
    from models.job_posting_knowledge_chunk import JobPostingKnowledgeChunk


class JobPostingKnowledgeSourceType(StrEnum):
    LEGAL_GUIDEBOOK = "LEGAL_GUIDEBOOK"
    LEGAL_MANUAL = "LEGAL_MANUAL"
    INSPECTION_CASE = "INSPECTION_CASE"
    LAW_TEXT = "LAW_TEXT"
    EXCEL_RISK_DATASET = "EXCEL_RISK_DATASET"
    WANTED_EVIDENCE = "WANTED_EVIDENCE"
    SYNTHETIC_CASE = "SYNTHETIC_CASE"


class KnowledgeProcessStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class JobPostingKnowledgeSource(Base, AuditBase):
    """
    채용공고 분석용 지식 원천 테이블.

    공정채용 가이드북, 채용절차법 PDF, 지도점검 사례 문서,
    엑셀 기반 리스크 데이터셋, 원티드 evidence 데이터 등
    RAG 검색에 사용할 원본 파일 또는 데이터셋 정보를 저장
    실제 검색 단위는 job_posting_knowledge_chunk 테이블에 저장
    """
    __tablename__ = "job_posting_knowledge_source"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    version_label: Mapped[str | None] = mapped_column(String(50), nullable=True)

    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_ext: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extract_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=KnowledgeProcessStatus.PENDING.value,
    )
    index_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=KnowledgeProcessStatus.PENDING.value,
    )

    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    metadata_json: Mapped[dict | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    chunks: Mapped[list["JobPostingKnowledgeChunk"]] = relationship(
        "JobPostingKnowledgeChunk",
        back_populates="knowledge_source",
        cascade="all, delete-orphan",
    )