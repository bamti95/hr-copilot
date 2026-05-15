"""LLM 호출 로그 조회 리포지토리.

면접 세션과 채용공고 분석 파이프라인에서 남긴 호출 로그를 조회하고 집계한다.
운영 대시보드와 추적 화면에서 쓰는 요약 지표도 이 파일에서 계산한다.
"""

from sqlalchemy import case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.candidate import Candidate
from models.interview_session import InterviewSession
from models.job_posting import JobPosting
from models.job_posting_analysis_report import JobPostingAnalysisReport
from models.llm_call_log import LlmCallLog
from repositories.base_repository import BaseRepository


class LlmCallLogRepository(BaseRepository[LlmCallLog]):
    """LLM 호출 로그의 상세 조회와 집계를 담당한다."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, LlmCallLog)

    async def find_by_session_id(self, session_id: int) -> list[LlmCallLog]:
        """면접 세션 1건의 로그를 실행 순서대로 반환한다."""
        stmt = (
            select(LlmCallLog)
            .where(
                LlmCallLog.interview_sessions_id == session_id,
                LlmCallLog.deleted_at.is_(None),
            )
            .order_by(
                LlmCallLog.execution_order.asc().nullslast(),
                LlmCallLog.id.asc(),
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def find_by_session_id_and_node_name(
        self,
        *,
        session_id: int,
        node_name: str,
    ) -> list[LlmCallLog]:
        """세션 안에서 특정 노드의 로그만 골라 반환한다."""
        stmt = (
            select(LlmCallLog)
            .where(
                LlmCallLog.interview_sessions_id == session_id,
                LlmCallLog.node_name == node_name,
                LlmCallLog.deleted_at.is_(None),
            )
            .order_by(
                LlmCallLog.execution_order.asc().nullslast(),
                LlmCallLog.id.asc(),
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def find_by_id_and_session_id(
        self,
        *,
        log_id: int,
        session_id: int,
    ) -> LlmCallLog | None:
        """세션 범위를 벗어나지 않도록 로그 1건을 조회한다."""
        stmt = (
            select(LlmCallLog)
            .where(
                LlmCallLog.id == log_id,
                LlmCallLog.interview_sessions_id == session_id,
                LlmCallLog.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_job_posting_analysis_report_id(
        self,
        report_id: int,
    ) -> list[LlmCallLog]:
        """채용공고 분석 리포트 1건에 연결된 로그를 순서대로 반환한다."""
        stmt = (
            select(LlmCallLog)
            .where(
                LlmCallLog.job_posting_analysis_report_id == report_id,
                LlmCallLog.pipeline_type == "JOB_POSTING_COMPLIANCE",
                LlmCallLog.deleted_at.is_(None),
            )
            .order_by(
                LlmCallLog.execution_order.asc().nullslast(),
                LlmCallLog.id.asc(),
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def find_by_job_posting_id(self, job_posting_id: int) -> list[LlmCallLog]:
        """채용공고 1건의 분석 로그를 최신 생성 시점 기준으로 조회한다."""
        stmt = (
            select(LlmCallLog)
            .where(
                LlmCallLog.job_posting_id == job_posting_id,
                LlmCallLog.pipeline_type == "JOB_POSTING_COMPLIANCE",
                LlmCallLog.deleted_at.is_(None),
            )
            .order_by(
                LlmCallLog.created_at.desc(),
                LlmCallLog.execution_order.asc().nullslast(),
                LlmCallLog.id.asc(),
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_usage_metrics_row(self, pipeline_type: str | None = None):
        """전체 사용량 요약 1행을 계산한다.

        토큰, 비용, 평균 지연 시간, 실패 호출 수를 한 번에 본다.
        """
        failed_call = case((LlmCallLog.call_status != "success", 1), else_=0)
        stmt = select(
            func.count(LlmCallLog.id),
            func.coalesce(func.sum(LlmCallLog.input_tokens), 0),
            func.coalesce(func.sum(LlmCallLog.output_tokens), 0),
            func.coalesce(func.sum(LlmCallLog.total_tokens), 0),
            func.coalesce(func.sum(LlmCallLog.estimated_cost), 0),
            func.coalesce(func.avg(LlmCallLog.elapsed_ms), 0),
            func.coalesce(func.sum(failed_call), 0),
        )
        if pipeline_type:
            stmt = stmt.where(LlmCallLog.pipeline_type == pipeline_type)
        result = await self.db.execute(stmt)
        return result.one()

    async def get_usage_by_node_rows(self, pipeline_type: str | None = None):
        """노드별 사용량을 비용 기준 내림차순으로 집계한다."""
        failed_call = case((LlmCallLog.call_status != "success", 1), else_=0)
        stmt = (
            select(
                func.coalesce(LlmCallLog.node_name, "unknown").label("node_name"),
                func.count(LlmCallLog.id),
                func.coalesce(func.sum(LlmCallLog.input_tokens), 0),
                func.coalesce(func.sum(LlmCallLog.output_tokens), 0),
                func.coalesce(func.sum(LlmCallLog.total_tokens), 0),
                func.coalesce(func.sum(LlmCallLog.estimated_cost), 0),
                func.coalesce(func.avg(LlmCallLog.elapsed_ms), 0),
                func.coalesce(func.sum(failed_call), 0),
            )
            .group_by(LlmCallLog.node_name)
            .order_by(desc(func.coalesce(func.sum(LlmCallLog.estimated_cost), 0)))
        )
        if pipeline_type:
            stmt = stmt.where(LlmCallLog.pipeline_type == pipeline_type)
        result = await self.db.execute(stmt)
        return result.all()

    async def get_usage_by_session_rows(self, limit: int, pipeline_type: str | None = None):
        """세션 단위 사용량을 조회한다.

        채용공고 분석 파이프라인은 세션 구조가 달라 별도 집계 함수로 위임한다.
        """
        if pipeline_type == "JOB_POSTING_COMPLIANCE":
            return await self.get_usage_by_job_posting_analysis_rows(limit)

        stmt = (
            select(
                LlmCallLog.interview_sessions_id,
                LlmCallLog.candidate_id,
                Candidate.name,
                InterviewSession.target_job,
                func.count(LlmCallLog.id),
                func.coalesce(func.sum(LlmCallLog.total_tokens), 0),
                func.coalesce(func.sum(LlmCallLog.estimated_cost), 0),
                func.coalesce(func.avg(LlmCallLog.elapsed_ms), 0),
                func.max(LlmCallLog.created_at),
            )
            .join(Candidate, Candidate.id == LlmCallLog.candidate_id)
            .join(InterviewSession, InterviewSession.id == LlmCallLog.interview_sessions_id)
            .group_by(
                LlmCallLog.interview_sessions_id,
                LlmCallLog.candidate_id,
                Candidate.name,
                InterviewSession.target_job,
            )
            .order_by(desc(func.max(LlmCallLog.created_at)))
            .limit(limit)
        )
        if pipeline_type:
            stmt = stmt.where(LlmCallLog.pipeline_type == pipeline_type)
        result = await self.db.execute(
            stmt
        )
        return result.all()

    async def get_usage_by_job_posting_analysis_rows(self, limit: int):
        """채용공고 분석 리포트 단위 사용량을 집계한다."""
        result = await self.db.execute(
            select(
                LlmCallLog.pipeline_type,
                LlmCallLog.target_type,
                LlmCallLog.target_id,
                LlmCallLog.job_posting_id,
                LlmCallLog.job_posting_analysis_report_id,
                JobPosting.job_title,
                JobPostingAnalysisReport.risk_level,
                func.count(LlmCallLog.id),
                func.coalesce(func.sum(LlmCallLog.total_tokens), 0),
                func.coalesce(func.sum(LlmCallLog.estimated_cost), 0),
                func.coalesce(func.avg(LlmCallLog.elapsed_ms), 0),
                func.max(LlmCallLog.created_at),
            )
            .outerjoin(JobPosting, JobPosting.id == LlmCallLog.job_posting_id)
            .outerjoin(
                JobPostingAnalysisReport,
                JobPostingAnalysisReport.id == LlmCallLog.job_posting_analysis_report_id,
            )
            .where(LlmCallLog.pipeline_type == "JOB_POSTING_COMPLIANCE")
            .group_by(
                LlmCallLog.pipeline_type,
                LlmCallLog.target_type,
                LlmCallLog.target_id,
                LlmCallLog.job_posting_id,
                LlmCallLog.job_posting_analysis_report_id,
                JobPosting.job_title,
                JobPostingAnalysisReport.risk_level,
            )
            .order_by(desc(func.max(LlmCallLog.created_at)))
            .limit(limit)
        )
        return result.all()

    async def get_recent_usage_rows(self, limit: int, pipeline_type: str | None = None):
        """최근 호출 로그를 최신순으로 가져온다."""
        stmt = (
            select(LlmCallLog, Candidate.name, JobPosting.job_title)
            .outerjoin(Candidate, Candidate.id == LlmCallLog.candidate_id)
            .outerjoin(JobPosting, JobPosting.id == LlmCallLog.job_posting_id)
            .order_by(desc(LlmCallLog.created_at))
            .limit(limit)
        )
        if pipeline_type:
            stmt = stmt.where(LlmCallLog.pipeline_type == pipeline_type)
        result = await self.db.execute(stmt)
        return result.all()
