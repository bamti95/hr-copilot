from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_active_manager
from models.manager import Manager
from schemas.llm_call_log import LlmCallLogListResponse, LlmCallLogResponse
from services.llm_call_log_service import LlmCallLogService

router = APIRouter(
    prefix="/interview-sessions",
    tags=["llm-call-log"],
)


@router.get(
    "/{session_id}/llm-logs",
    response_model=LlmCallLogListResponse,
)
async def get_session_llm_logs(
    session_id: int,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> LlmCallLogListResponse:
    service = LlmCallLogService(db)
    return await service.get_session_logs(session_id)


@router.get(
    "/{session_id}/llm-logs/nodes/{node_name}",
    response_model=LlmCallLogListResponse,
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
    "/{session_id}/llm-logs/{log_id}",
    response_model=LlmCallLogResponse,
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
