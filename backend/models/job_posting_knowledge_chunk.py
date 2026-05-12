from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.audit_base import AuditBase
from models.base import Base

try:
    from pgvector.sqlalchemy import Vector
except ModuleNotFoundError:
    def Vector(_: int):
        return JSONB

if TYPE_CHECKING:
    from models.job_posting_knowledge_source import JobPostingKnowledgeSource


class JobPostingKnowledgeChunkType(StrEnum):
    LEGAL_CLAUSE = "LEGAL_CLAUSE"
    LEGAL_GUIDE = "LEGAL_GUIDE"
    LEGAL_CHECKLIST = "LEGAL_CHECKLIST"
    INSPECTION_CASE = "INSPECTION_CASE"
    RISK_PATTERN_ROW = "RISK_PATTERN_ROW"
    EVIDENCE_CARD = "EVIDENCE_CARD"
    SYNTHETIC_CASE = "SYNTHETIC_CASE"


class JobPostingRiskSeverity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    WARN = "WARN"


class JobPostingKnowledgeChunk(Base, AuditBase):
    """
    채용공고 분석용 RAG chunk 테이블.

    PDF 법령/가이드 문서에서 추출한 조항, 체크리스트, 위반 사례와
    엑셀 데이터셋의 row 단위 리스크 패턴을 저장
    pgvector embedding을 함께 저장하여 채용공고 분석 시
    유사한 법령 근거, 위반 사례, 리스크 패턴을 검색하는 데 사용
    """
    __tablename__ = "job_posting_knowledge_chunk"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    knowledge_source_id: Mapped[int] = mapped_column(
        ForeignKey("job_posting_knowledge_source.id"),
        nullable=False,
    )

    chunk_type: Mapped[str] = mapped_column(String(50), nullable=False)
    chunk_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sheet_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    row_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    issue_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    risk_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    severity: Mapped[str | None] = mapped_column(String(30), nullable=True)

    law_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    article_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    penalty_guide: Mapped[str | None] = mapped_column(Text, nullable=True)

    violation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    violation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    correction_suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)

    tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )

    embedding_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)

    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    use_tf: Mapped[str] = mapped_column(String(1), nullable=False, default="Y")
    del_tf: Mapped[str] = mapped_column(String(1), nullable=False, default="N")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    knowledge_source: Mapped["JobPostingKnowledgeSource"] = relationship(
        "JobPostingKnowledgeSource",
        back_populates="chunks",
    )
