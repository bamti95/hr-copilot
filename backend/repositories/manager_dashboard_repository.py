"""관리자 대시보드 집계 전용 리포지토리.

문서 처리, 질문 생성, 검토 상태, LLM 비용처럼 대시보드에 바로 쓰는 숫자를 모은다.
화면에서 필요한 묶음 기준에 맞춰 count와 최근 활동 목록을 함께 제공한다.
"""

from typing import Any
from datetime import datetime

from sqlalchemy import and_, case, desc, distinct, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.ai_job import AiJob, AiJobStatus, AiJobType
from models.candidate import Candidate
from models.document import Document
from models.interview_question import InterviewQuestion
from models.interview_session import InterviewSession
from models.job_posting import JobPosting
from models.job_posting_analysis_report import JobPostingAnalysisReport
from models.job_posting_knowledge_source import JobPostingKnowledgeSource
from models.llm_call_log import LlmCallLog

# 문서 추출이 아직 끝나지 않은 상태 코드 묶음이다.
PENDING_DOCUMENT_STATUSES = {"PENDING", "PROCESSING"}
FAILED_DOCUMENT_STATUSES = {"FAILED"}
PENDING_QUESTION_STATUSES = {"NOT_REQUESTED", "QUEUED", "PROCESSING"}
FAILED_QUESTION_STATUSES = {"FAILED"}
PARTIAL_QUESTION_STATUSES = {"PARTIAL_COMPLETED"}
COMPLETED_QUESTION_STATUSES = {"COMPLETED"}
REVIEW_PROBLEM_STATUSES = {"needs_revision", "rejected"}
ACTIVE_JOB_STATUSES = {
    AiJobStatus.QUEUED.value,
    AiJobStatus.RUNNING.value,
    AiJobStatus.RETRYING.value,
}
JOB_POSTING_REVIEW_RISK_LEVELS = {"HIGH", "MEDIUM", "CRITICAL"}


class ManagerDashboardRepository:
    """관리자 대시보드용 집계 쿼리를 모아 둔 객체."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _scalar_int(self, stmt: Any) -> int:
        """정수형 집계 결과를 일관된 형식으로 변환한다."""
        return int((await self.db.execute(stmt)).scalar_one() or 0)

    async def count_document_pending(self) -> int:
        """처리 대기 중인 문서 수를 센다."""
        return await self._scalar_int(
            select(func.count(Document.id)).where(
                Document.deleted_at.is_(None),
                Document.extract_status.in_(PENDING_DOCUMENT_STATUSES),
            )
        )

    async def count_document_failed(self) -> int:
        """처리 실패 문서 수를 센다."""
        return await self._scalar_int(
            select(func.count(Document.id)).where(
                Document.deleted_at.is_(None),
                Document.extract_status.in_(FAILED_DOCUMENT_STATUSES),
            )
        )

    async def count_document_analyzed_candidates(self) -> int:
        """문서 분석이 완료된 후보자 수를 센다."""
        return await self._scalar_int(
            select(func.count(distinct(Document.candidate_id))).where(
                Document.deleted_at.is_(None),
                or_(
                    Document.extract_status == "COMPLETED",
                    and_(
                        Document.extracted_text.is_not(None),
                        func.length(func.trim(Document.extracted_text)) > 0,
                    ),
                ),
            )
        )

    async def count_question_pending_sessions(self) -> int:
        """질문 생성이 아직 끝나지 않은 세션 수를 센다."""
        return await self._scalar_int(
            select(func.count(InterviewSession.id)).where(
                InterviewSession.deleted_at.is_(None),
                InterviewSession.question_generation_status.in_(
                    PENDING_QUESTION_STATUSES
                ),
            )
        )

    async def count_question_failed_sessions(self) -> int:
        """질문 생성 실패 세션 수를 센다."""
        return await self._scalar_int(
            select(func.count(InterviewSession.id)).where(
                InterviewSession.deleted_at.is_(None),
                InterviewSession.question_generation_status.in_(FAILED_QUESTION_STATUSES),
            )
        )

    async def count_partial_sessions(self) -> int:
        """질문 생성이 일부만 끝난 세션 수를 센다."""
        return await self._scalar_int(
            select(func.count(InterviewSession.id)).where(
                InterviewSession.deleted_at.is_(None),
                InterviewSession.question_generation_status.in_(
                    PARTIAL_QUESTION_STATUSES
                ),
            )
        )

    async def count_review_problem_sessions(self) -> int:
        """재검토가 필요한 세션 수를 센다.

        명시적 반려 상태와 저점수 질문을 함께 본다.
        """
        return await self._scalar_int(
            select(func.count(distinct(InterviewQuestion.interview_sessions_id))).where(
                InterviewQuestion.deleted_at.is_(None),
                or_(
                    InterviewQuestion.review_status.in_(REVIEW_PROBLEM_STATUSES),
                    InterviewQuestion.score < 80,
                ),
            )
        )

    async def count_candidates(self) -> int:
        """활성 후보자 수를 센다."""
        return await self._scalar_int(
            select(func.count(Candidate.id)).where(Candidate.deleted_at.is_(None))
        )

    async def count_document_uploaded_candidates(self) -> int:
        """문서를 한 건 이상 올린 후보자 수를 센다."""
        return await self._scalar_int(
            select(func.count(distinct(Document.candidate_id))).where(
                Document.deleted_at.is_(None)
            )
        )

    async def count_sessions(self) -> int:
        """활성 면접 세션 수를 센다."""
        return await self._scalar_int(
            select(func.count(InterviewSession.id)).where(
                InterviewSession.deleted_at.is_(None)
            )
        )

    async def count_question_completed_sessions(self) -> int:
        """질문 생성 완료 세션 수를 센다."""
        return await self._scalar_int(
            select(func.count(InterviewSession.id)).where(
                InterviewSession.deleted_at.is_(None),
                InterviewSession.question_generation_status.in_(
                    COMPLETED_QUESTION_STATUSES
                ),
            )
        )

    async def count_review_passed_sessions(self) -> int:
        """승인 질문이 일정 개수 이상인 세션 수를 센다.

        현재 기준은 승인 질문 5개 이상이다.
        """
        approved_question_count = func.sum(
            case((InterviewQuestion.review_status == "approved", 1), else_=0)
        )
        return await self._scalar_int(
            select(func.count()).select_from(
                select(InterviewQuestion.interview_sessions_id)
                .where(InterviewQuestion.deleted_at.is_(None))
                .group_by(InterviewQuestion.interview_sessions_id)
                .having(func.coalesce(approved_question_count, 0) >= 5)
                .subquery()
            )
        )

    async def get_priority_session_rows(self):
        """우선 확인이 필요한 세션 목록 원본 행을 반환한다."""
        result = await self.db.execute(
            select(
                InterviewSession.id,
                InterviewSession.candidate_id,
                Candidate.name,
                InterviewSession.target_job,
                InterviewSession.question_generation_status,
                InterviewSession.question_generation_error,
                InterviewSession.created_at,
                InterviewSession.question_generation_requested_at,
                InterviewSession.question_generation_completed_at,
                func.min(InterviewQuestion.score),
                func.sum(
                    case((InterviewQuestion.review_status == "rejected", 1), else_=0)
                ),
                func.sum(
                    case(
                        (InterviewQuestion.review_status == "needs_revision", 1),
                        else_=0,
                    )
                ),
            )
            .join(Candidate, Candidate.id == InterviewSession.candidate_id)
            .outerjoin(
                InterviewQuestion,
                and_(
                    InterviewQuestion.interview_sessions_id == InterviewSession.id,
                    InterviewQuestion.deleted_at.is_(None),
                ),
            )
            .where(
                InterviewSession.deleted_at.is_(None),
                Candidate.deleted_at.is_(None),
            )
            .group_by(
                InterviewSession.id,
                InterviewSession.candidate_id,
                Candidate.name,
                InterviewSession.target_job,
                InterviewSession.question_generation_status,
                InterviewSession.question_generation_error,
                InterviewSession.created_at,
                InterviewSession.question_generation_requested_at,
                InterviewSession.question_generation_completed_at,
            )
        )
        return result.all()

    async def get_candidates_without_session_rows(self, limit: int = 10):
        """아직 면접 세션이 없는 후보자 최근 목록을 가져온다."""
        result = await self.db.execute(
            select(Candidate.id, Candidate.name, Candidate.job_position, Candidate.updated_at)
            .outerjoin(
                InterviewSession,
                and_(
                    InterviewSession.candidate_id == Candidate.id,
                    InterviewSession.deleted_at.is_(None),
                ),
            )
            .where(
                Candidate.deleted_at.is_(None),
                InterviewSession.id.is_(None),
            )
            .order_by(desc(Candidate.updated_at))
            .limit(limit)
        )
        return result.all()

    async def get_document_failed_candidate_rows(self, limit: int = 10):
        """문서 추출이 실패한 후보자 최근 목록을 가져온다."""
        result = await self.db.execute(
            select(
                Candidate.id,
                Candidate.name,
                Candidate.job_position,
                Candidate.updated_at,
            )
            .join(Document, Document.candidate_id == Candidate.id)
            .where(
                Candidate.deleted_at.is_(None),
                Document.deleted_at.is_(None),
                Document.extract_status.in_(FAILED_DOCUMENT_STATUSES),
            )
            .group_by(Candidate.id, Candidate.name, Candidate.job_position, Candidate.updated_at)
            .order_by(desc(Candidate.updated_at))
            .limit(limit)
        )
        return result.all()

    async def get_recent_session_rows(self, limit: int = 8):
        """최근 생성된 세션 목록과 질문 수를 함께 조회한다."""
        question_count = func.count(InterviewQuestion.id)
        result = await self.db.execute(
            select(
                InterviewSession.id,
                InterviewSession.candidate_id,
                Candidate.name,
                InterviewSession.target_job,
                InterviewSession.question_generation_status,
                question_count,
                InterviewSession.created_at,
            )
            .join(Candidate, Candidate.id == InterviewSession.candidate_id)
            .outerjoin(
                InterviewQuestion,
                and_(
                    InterviewQuestion.interview_sessions_id == InterviewSession.id,
                    InterviewQuestion.deleted_at.is_(None),
                ),
            )
            .where(
                InterviewSession.deleted_at.is_(None),
                Candidate.deleted_at.is_(None),
            )
            .group_by(
                InterviewSession.id,
                InterviewSession.candidate_id,
                Candidate.name,
                InterviewSession.target_job,
                InterviewSession.question_generation_status,
                InterviewSession.created_at,
            )
            .order_by(desc(InterviewSession.created_at))
            .limit(limit)
        )
        return result.all()

    async def get_recent_candidate_activity_rows(self, limit: int = 8):
        """최근 등록된 후보자 목록을 가져온다."""
        result = await self.db.execute(
            select(Candidate.id, Candidate.name, Candidate.job_position, Candidate.created_at)
            .where(Candidate.deleted_at.is_(None))
            .order_by(desc(Candidate.created_at))
            .limit(limit)
        )
        return result.all()

    async def get_recent_document_activity_rows(self, limit: int = 8):
        """최근 업로드된 문서 목록을 가져온다."""
        result = await self.db.execute(
            select(
                Document.id,
                Document.candidate_id,
                Candidate.name,
                Document.title,
                Document.created_at,
            )
            .join(Candidate, Candidate.id == Document.candidate_id)
            .where(Document.deleted_at.is_(None), Candidate.deleted_at.is_(None))
            .order_by(desc(Document.created_at))
            .limit(limit)
        )
        return result.all()

    async def get_recent_session_activity_rows(self, limit: int = 8):
        """최근 생성된 세션 활동 목록을 가져온다."""
        result = await self.db.execute(
            select(
                InterviewSession.id,
                InterviewSession.candidate_id,
                Candidate.name,
                InterviewSession.target_job,
                InterviewSession.created_at,
                InterviewSession.question_generation_requested_at,
                InterviewSession.question_generation_completed_at,
                InterviewSession.question_generation_status,
            )
            .join(Candidate, Candidate.id == InterviewSession.candidate_id)
            .where(InterviewSession.deleted_at.is_(None), Candidate.deleted_at.is_(None))
            .order_by(desc(InterviewSession.created_at))
            .limit(limit)
        )
        return result.all()

    async def get_recent_question_activity_rows(self, limit: int = 8):
        """최근 생성된 질문 활동 목록을 가져온다."""
        result = await self.db.execute(
            select(
                InterviewQuestion.id,
                InterviewQuestion.interview_sessions_id,
                Candidate.name,
                InterviewQuestion.category,
                InterviewQuestion.created_at,
            )
            .join(
                InterviewSession,
                InterviewSession.id == InterviewQuestion.interview_sessions_id,
            )
            .join(Candidate, Candidate.id == InterviewSession.candidate_id)
            .where(
                InterviewQuestion.deleted_at.is_(None),
                InterviewSession.deleted_at.is_(None),
                Candidate.deleted_at.is_(None),
            )
            .order_by(desc(InterviewQuestion.created_at))
            .limit(limit)
        )
        return result.all()

    async def get_llm_cost_metrics_row(
        self,
        *,
        today_start: datetime,
        month_start: datetime,
    ):
        """LLM 비용 대시보드 상단 요약 1행을 계산한다.

        오늘 기준 수치와 월 기준 누적 수치를 함께 반환한다.
        로컬 모델은 비용 집계 대상에서 제외한다.
        """
        failed_call = case((LlmCallLog.call_status != "success", 1), else_=0)
        today_cost = func.sum(
            case(
                (LlmCallLog.created_at >= today_start, LlmCallLog.estimated_cost),
                else_=0,
            )
        )
        today_calls = func.sum(
            case((LlmCallLog.created_at >= today_start, 1), else_=0)
        )
        today_failed_calls = func.sum(
            case((LlmCallLog.created_at >= today_start, failed_call), else_=0)
        )
        today_tokens = func.sum(
            case(
                (LlmCallLog.created_at >= today_start, LlmCallLog.total_tokens),
                else_=0,
            )
        )

        result = await self.db.execute(
            select(
                func.coalesce(today_cost, 0),
                func.coalesce(func.sum(LlmCallLog.estimated_cost), 0),
                func.coalesce(today_calls, 0),
                func.coalesce(today_failed_calls, 0),
                func.coalesce(today_tokens, 0),
                func.coalesce(func.avg(LlmCallLog.elapsed_ms), 0),
            ).where(
                LlmCallLog.deleted_at.is_(None),
                LlmCallLog.model_name != "local",
                LlmCallLog.created_at >= month_start,
            )
        )
        return result.one()

    async def get_llm_top_cost_node_rows(
        self,
        *,
        month_start: datetime,
        limit: int = 5,
    ):
        """월 기준 비용 상위 노드를 집계한다."""
        result = await self.db.execute(
            select(
                func.coalesce(LlmCallLog.node_name, "unknown").label("node_name"),
                func.count(LlmCallLog.id),
                func.coalesce(func.sum(LlmCallLog.total_tokens), 0),
                func.coalesce(func.sum(LlmCallLog.estimated_cost), 0),
                func.coalesce(func.avg(LlmCallLog.elapsed_ms), 0),
            )
            .where(
                LlmCallLog.deleted_at.is_(None),
                LlmCallLog.model_name != "local",
                LlmCallLog.created_at >= month_start,
            )
            .group_by(LlmCallLog.node_name)
            .order_by(desc(func.coalesce(func.sum(LlmCallLog.estimated_cost), 0)))
            .limit(limit)
        )
        return result.all()

    async def count_job_postings(self) -> int:
        """등록된 채용공고 수를 센다."""
        return await self._scalar_int(
            select(func.count(JobPosting.id)).where(JobPosting.deleted_at.is_(None))
        )

    async def count_job_posting_analyzed(self) -> int:
        """성공 리포트가 하나 이상 있는 채용공고 수를 센다."""
        return await self._scalar_int(
            select(func.count(distinct(JobPostingAnalysisReport.job_posting_id))).where(
                JobPostingAnalysisReport.deleted_at.is_(None),
                JobPostingAnalysisReport.analysis_status == "SUCCESS",
            )
        )

    async def count_job_posting_pending_analysis(self) -> int:
        """대기 또는 실행 중인 채용공고 분석 작업 수를 센다."""
        return await self._scalar_int(
            select(func.count(AiJob.id)).where(
                AiJob.deleted_at.is_(None),
                AiJob.job_type == AiJobType.JOB_POSTING_COMPLIANCE_ANALYSIS.value,
                AiJob.status.in_(ACTIVE_JOB_STATUSES),
            )
        )

    async def count_job_posting_failed_analysis(self) -> int:
        """실패한 채용공고 분석 리포트 수를 센다."""
        return await self._scalar_int(
            select(func.count(JobPostingAnalysisReport.id)).where(
                JobPostingAnalysisReport.deleted_at.is_(None),
                JobPostingAnalysisReport.analysis_status == "FAILED",
            )
        )

    async def count_job_posting_review_required(self) -> int:
        """리스크 또는 이슈가 있어 매니저 확인이 필요한 공고 수를 센다."""
        return await self._scalar_int(
            select(func.count(distinct(JobPostingAnalysisReport.job_posting_id))).where(
                JobPostingAnalysisReport.deleted_at.is_(None),
                JobPostingAnalysisReport.analysis_status == "SUCCESS",
                or_(
                    JobPostingAnalysisReport.issue_count > 0,
                    JobPostingAnalysisReport.violation_count > 0,
                    JobPostingAnalysisReport.warning_count > 0,
                    JobPostingAnalysisReport.risk_level.in_(
                        JOB_POSTING_REVIEW_RISK_LEVELS
                    ),
                ),
            )
        )

    async def count_job_posting_knowledge_sources(self) -> int:
        """RAG 기반지식 원천 문서 수를 센다."""
        return await self._scalar_int(
            select(func.count(JobPostingKnowledgeSource.id)).where(
                JobPostingKnowledgeSource.deleted_at.is_(None)
            )
        )

    async def count_job_posting_indexed_knowledge_sources(self) -> int:
        """색인이 완료된 RAG 기반지식 문서 수를 센다."""
        return await self._scalar_int(
            select(func.count(JobPostingKnowledgeSource.id)).where(
                JobPostingKnowledgeSource.deleted_at.is_(None),
                JobPostingKnowledgeSource.index_status == "SUCCESS",
            )
        )

    async def get_job_posting_llm_cost_metrics_row(
        self,
        *,
        today_start: datetime,
        month_start: datetime,
    ):
        """채용공고 분석 파이프라인의 오늘/월 비용과 평균 분석 비용을 계산한다."""
        today_cost = func.sum(
            case(
                (LlmCallLog.created_at >= today_start, LlmCallLog.estimated_cost),
                else_=0,
            )
        )
        result = await self.db.execute(
            select(
                func.coalesce(today_cost, 0),
                func.coalesce(func.sum(LlmCallLog.estimated_cost), 0),
                func.coalesce(
                    func.sum(LlmCallLog.estimated_cost)
                    / func.nullif(
                        func.count(distinct(LlmCallLog.job_posting_analysis_report_id)),
                        0,
                    ),
                    0,
                ),
            ).where(
                LlmCallLog.deleted_at.is_(None),
                LlmCallLog.model_name != "local",
                LlmCallLog.pipeline_type == "JOB_POSTING_COMPLIANCE",
                LlmCallLog.created_at >= month_start,
            )
        )
        return result.one()

    async def get_recent_job_posting_report_rows(self, limit: int = 6):
        """최근 채용공고 분석 리포트 목록을 반환한다."""
        result = await self.db.execute(
            select(
                JobPostingAnalysisReport.id,
                JobPostingAnalysisReport.job_posting_id,
                JobPosting.job_title,
                JobPosting.company_name,
                JobPostingAnalysisReport.analysis_status,
                JobPostingAnalysisReport.risk_level,
                JobPostingAnalysisReport.issue_count,
                JobPostingAnalysisReport.violation_count,
                JobPostingAnalysisReport.warning_count,
                JobPostingAnalysisReport.updated_at,
            )
            .join(JobPosting, JobPosting.id == JobPostingAnalysisReport.job_posting_id)
            .where(
                JobPostingAnalysisReport.deleted_at.is_(None),
                JobPosting.deleted_at.is_(None),
            )
            .order_by(
                desc(JobPostingAnalysisReport.updated_at),
                desc(JobPostingAnalysisReport.id),
            )
            .limit(limit)
        )
        return result.all()
