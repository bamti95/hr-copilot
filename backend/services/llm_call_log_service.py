from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.llm_call_log_repository import LlmCallLogRepository
from schemas.llm_call_log import LlmCallLogListResponse, LlmCallLogResponse


class LlmCallLogService:
    def __init__(self, db: AsyncSession):
        self.repository = LlmCallLogRepository(db)

    async def get_session_logs(self, session_id: int) -> LlmCallLogListResponse:
        logs = await self.repository.find_by_session_id(session_id)
        items = [LlmCallLogResponse.from_entity(log) for log in logs]
        return LlmCallLogListResponse.of(session_id=session_id, items=items)

    async def get_session_node_logs(
        self,
        *,
        session_id: int,
        node_name: str,
    ) -> LlmCallLogListResponse:
        logs = await self.repository.find_by_session_id_and_node_name(
            session_id=session_id,
            node_name=node_name,
        )
        items = [LlmCallLogResponse.from_entity(log) for log in logs]
        return LlmCallLogListResponse.of(session_id=session_id, items=items)

    async def get_log_detail(
        self,
        *,
        session_id: int,
        log_id: int,
    ) -> LlmCallLogResponse:
        log = await self.repository.find_by_id_and_session_id(
            log_id=log_id,
            session_id=session_id,
        )
        if log is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LLM call log not found.",
            )
        return LlmCallLogResponse.from_entity(log)
