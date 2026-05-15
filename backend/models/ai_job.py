"""백그라운드 AI 작업 상태를 저장하는 모델이다."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.audit_base import AuditBase
from models.base import Base


class AiJobType(StrEnum):
    # 지원자 Excel/CSV 일괄 등록 작업
    BULK_CANDIDATE_IMPORT = "BULK_CANDIDATE_IMPORT"

    # 지원자 문서 ZIP/다중 파일 기반 일괄 등록 미리보기/확정 작업
    DOCUMENT_BULK_IMPORT = "DOCUMENT_BULK_IMPORT"
    
    # 업로드된 문서의 텍스트 추출/파싱 작업
    DOCUMENT_EXTRACTION = "DOCUMENT_EXTRACTION"
    
    # 면접 세션 기준 신규 면접 질문 생성 작업
    QUESTION_GENERATION = "QUESTION_GENERATION"
    
    # 기존 생성 질문 중 일부 또는 전체를 다시 생성하는 작업
    QUESTION_REGENERATION = "QUESTION_REGENERATION"
    
    # 지원자 분석 결과와 질문 품질 점수를 기반으로 면접 대상자 추천 랭킹을 계산하는 작업
    CANDIDATE_RANKING = "CANDIDATE_RANKING"
    
    # 채용공고 1건을 분석해서 컴플라이언스/리스크 검증 리포트를 생성하는 작업
    JOB_POSTING_COMPLIANCE_ANALYSIS = "JOB_POSTING_COMPLIANCE_ANALYSIS"
    
    # 채용공고 리스크 분석에 사용할 법령/가이드북/지도점검 사례 문서를 RAG 검색 가능하게 색인하는 작업
    JOB_POSTING_KNOWLEDGE_INDEXING = "JOB_POSTING_KNOWLEDGE_INDEXING"
    JOB_POSTING_EXPERIMENT_RUN = "JOB_POSTING_EXPERIMENT_RUN"


class AiJobStatus(StrEnum):
    # 작업이 생성되었고 아직 실행 대기 중인 상태
    QUEUED = "QUEUED"

    # 작업이 현재 실행 중인 상태
    RUNNING = "RUNNING"

    # 작업이 정상적으로 완료된 상태
    SUCCESS = "SUCCESS"

    # 작업 일부는 성공했지만 일부 대상에서 실패가 발생한 상태
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"

    # 작업 실행 중 오류가 발생해 실패한 상태
    FAILED = "FAILED"

    # 실패한 작업을 재시도 대기 또는 재실행 중인 상태
    RETRYING = "RETRYING"

    # 실행 전 또는 관리자의 요청으로 작업이 취소된 상태
    CANCELLED = "CANCELLED"


class AiJobTargetType(StrEnum):
    # 작업 대상이 지원자 단위인 경우
    CANDIDATE = "CANDIDATE"

    # 작업 대상이 업로드 문서 단위인 경우
    DOCUMENT = "DOCUMENT"

    # 작업 대상이 면접 세션 단위인 경우
    INTERVIEW_SESSION = "INTERVIEW_SESSION"

    # 작업 대상이 지원자 일괄 등록 묶음인 경우
    BULK_IMPORT = "BULK_IMPORT"
    
    # 채용공고 원문 자체
    JOB_POSTING = "JOB_POSTING"
    
    # 법령/가이드북/지도점검 사례 같은 지식 원천 문서
    KNOWLEDGE_SOURCE = "KNOWLEDGE_SOURCE"


class AiJob(Base, AuditBase):
    """
    BackgroundTasks 기반 AI/일괄 작업의 상태 원장(source of truth).

    ai_job이 담당하는 역할:
    1. 어떤 작업이 요청되었는가: job_type
    2. 누가 요청했는가: requested_by, created_by
    3. 어떤 대상에 대한 작업인가: target_type, target_id, candidate_id,
       document_id, interview_session_id
    4. 현재 상태가 무엇인가: status
    5. 어디까지 진행되었는가: progress, current_step
    6. 실패했는가: status=FAILED, error_message
    7. 재시도 가능한가: attempt_count, max_attempts, status
    8. 중복 실행을 막을 수 있는가: 활성 job 조회 및 DB unique index 기준
    9. 프론트에서 진행률을 조회할 수 있는가: progress, current_step,
       result_payload, error_message

    BackgroundTasks는 실행 엔진으로만 사용하고, 작업 상태의 기준은 이 테이블에 둔다.
    interview_sessions.question_generation_status는 질문 생성 도메인의 표시/호환 상태로
    ai_job 상태와 동기화한다.
    """

    __tablename__ = "ai_job"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=AiJobStatus.QUEUED.value,
        server_default=AiJobStatus.QUEUED.value,
    )

    target_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    candidate_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidate.id"),
        nullable=True,
    )
    document_id: Mapped[int | None] = mapped_column(
        ForeignKey("document.id"),
        nullable=True,
    )
    interview_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("interview_sessions.id"),
        nullable=True,
    )
    parent_job_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_job.id"),
        nullable=True,
    )

    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_step: Mapped[str | None] = mapped_column(String(100), nullable=True)

    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    request_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    requested_by: Mapped[int | None] = mapped_column(
        ForeignKey("manager.id"),
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

