"""LLM 호출 로그 조회 서비스를 제공한다.

면접 세션과 채용공고 분석에 연결된 LLM 호출 로그를 조회한다.
조회 전에 대상 리소스가 실제로 존재하는지 먼저 확인해,
잘못된 ID로 인한 조회를 초기에 막는 것이 핵심 규칙이다.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.llm_call_log_repository import LlmCallLogRepository
from repositories.job_posting_repository import JobPostingAnalysisReportRepository, JobPostingRepository
from repositories.session_repo import SessionRepository
from schemas.llm_call_log import LlmCallLogListResponse, LlmCallLogResponse


def _http_error(status_code: int, code: str, message: str) -> HTTPException:
    """서비스 전반에서 공통으로 쓰는 HTTP 예외 형식을 만든다."""
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
    )


class LlmCallLogService:
    """LLM 호출 로그 조회 전용 서비스다.

    로그를 직접 가공하기보다, 조회 대상이 맞는지 검증하고
    응답 스키마로 변환해 API 계층에 넘기는 역할을 맡는다.
    """

    def __init__(self, db: AsyncSession):
        self.repository = LlmCallLogRepository(db)
        self.session_repository = SessionRepository(db)
        self.job_posting_repository = JobPostingRepository(db)
        self.report_repository = JobPostingAnalysisReportRepository(db)

    async def _ensure_session_exists(self, session_id: int) -> None:
        """세션 기반 로그 조회 전에 세션 존재 여부를 보장한다."""
        session = await self.session_repository.find_by_id_not_deleted(session_id)
        if session is None:
            raise _http_error(
                status.HTTP_404_NOT_FOUND,
                "SESSION_NOT_FOUND",
                "면접 세션을 찾을 수 없습니다.",
            )

    async def get_session_logs(self, session_id: int) -> LlmCallLogListResponse:
        """특정 면접 세션에 연결된 전체 LLM 로그를 반환한다."""
        await self._ensure_session_exists(session_id)
        logs = await self.repository.find_by_session_id(session_id)
        items = [LlmCallLogResponse.from_entity(log) for log in logs]
        return LlmCallLogListResponse.of(session_id=session_id, items=items)

    async def get_session_node_logs(
        self,
        *,
        session_id: int,
        node_name: str,
    ) -> LlmCallLogListResponse:
        """세션 내부의 특정 노드 로그만 골라서 반환한다.

        같은 세션이라도 노드별 호출 맥락이 다르므로,
        디버깅 시에는 전체 로그보다 이 조회가 더 직접적이다.
        """
        await self._ensure_session_exists(session_id)
        logs = await self.repository.find_by_session_id_and_node_name(
            session_id=session_id,
            node_name=node_name,
        )
        if not logs:
            raise _http_error(
                status.HTTP_404_NOT_FOUND,
                "NODE_NOT_FOUND",
                "해당 노드의 로그를 찾을 수 없습니다.",
            )
        items = [LlmCallLogResponse.from_entity(log) for log in logs]
        return LlmCallLogListResponse.of(session_id=session_id, items=items)

    async def get_log_detail(
        self,
        *,
        session_id: int,
        log_id: int,
    ) -> LlmCallLogResponse:
        """세션 범위를 벗어나지 않는 단일 로그 상세를 반환한다."""
        await self._ensure_session_exists(session_id)
        log = await self.repository.find_by_id_and_session_id(
            log_id=log_id,
            session_id=session_id,
        )
        if log is None:
            raise _http_error(
                status.HTTP_404_NOT_FOUND,
                "LOG_NOT_FOUND",
                "LLM 호출 로그를 찾을 수 없습니다.",
            )
        return LlmCallLogResponse.from_entity(log)

    async def get_job_posting_analysis_logs(
        self,
        report_id: int,
    ) -> LlmCallLogListResponse:
        """채용공고 분석 리포트에 연결된 LLM 로그를 반환한다."""
        report = await self.report_repository.find_by_id_not_deleted(report_id)
        if report is None:
            raise _http_error(
                status.HTTP_404_NOT_FOUND,
                "REPORT_NOT_FOUND",
                "Job posting analysis report was not found.",
            )
        logs = await self.repository.find_by_job_posting_analysis_report_id(report_id)
        items = [LlmCallLogResponse.from_entity(log) for log in logs]
        return LlmCallLogListResponse.of(session_id=report_id, items=items)

    async def get_job_posting_logs(
        self,
        job_posting_id: int,
    ) -> LlmCallLogListResponse:
        """채용공고 단위로 누적된 LLM 호출 로그를 반환한다."""
        posting = await self.job_posting_repository.find_by_id_not_deleted(job_posting_id)
        if posting is None:
            raise _http_error(
                status.HTTP_404_NOT_FOUND,
                "JOB_POSTING_NOT_FOUND",
                "Job posting was not found.",
            )
        logs = await self.repository.find_by_job_posting_id(job_posting_id)
        items = [LlmCallLogResponse.from_entity(log) for log in logs]
        return LlmCallLogListResponse.of(session_id=job_posting_id, items=items)
