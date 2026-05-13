from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_active_manager
from models.manager import Manager
from schemas.llm_call_log import LlmCallLogListResponse, LlmCallLogResponse
from services.llm_call_log_service import LlmCallLogService

router = APIRouter(tags=["AI 호출 로그 관리"])


@router.get(
    "/llm-logs/interview-sessions/{session_id}",
    response_model=LlmCallLogListResponse,
    summary="면접 세션 LLM 호출 로그 목록 조회",
)
async def get_session_llm_logs(
    session_id: int,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> LlmCallLogListResponse:
    service = LlmCallLogService(db)
    return await service.get_session_logs(session_id)


@router.get(
    "/llm-logs/interview-sessions/{session_id}/nodes/{node_name}",
    response_model=LlmCallLogListResponse,
    summary="면접 세션 노드별 LLM 호출 로그 조회",
)
async def get_session_node_logs(
    session_id: int,
    node_name: str,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> LlmCallLogListResponse:
    service = LlmCallLogService(db)
    return await service.get_session_node_logs(
        session_id=session_id,
        node_name=node_name,
    )


@router.get(
    "/llm-logs/interview-sessions/{session_id}/logs/{log_id}",
    response_model=LlmCallLogResponse,
    summary="면접 세션 LLM 호출 로그 상세 조회",
)
async def get_session_llm_log_detail(
    session_id: int,
    log_id: int,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> LlmCallLogResponse:
    service = LlmCallLogService(db)
    return await service.get_log_detail(
        session_id=session_id,
        log_id=log_id,
    )


@router.get(
    "/llm-logs/job-posting-analysis-reports/{report_id}",
    response_model=LlmCallLogListResponse,
    summary="Job posting compliance workflow logs by report",
)
async def get_job_posting_analysis_logs(
    report_id: int,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> LlmCallLogListResponse:
    service = LlmCallLogService(db)
    return await service.get_job_posting_analysis_logs(report_id)


@router.get(
    "/llm-logs/job-postings/{job_posting_id}",
    response_model=LlmCallLogListResponse,
    summary="Job posting compliance workflow logs by job posting",
)
async def get_job_posting_logs(
    job_posting_id: int,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> LlmCallLogListResponse:
    service = LlmCallLogService(db)
    return await service.get_job_posting_logs(job_posting_id)
