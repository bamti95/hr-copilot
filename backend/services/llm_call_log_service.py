from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.llm_call_log_repository import LlmCallLogRepository
from repositories.session_repo import SessionRepository
from schemas.llm_call_log import LlmCallLogListResponse, LlmCallLogResponse


def _http_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
    )


class LlmCallLogService:
    def __init__(self, db: AsyncSession):
        self.repository = LlmCallLogRepository(db)
        self.session_repository = SessionRepository(db)

    async def _ensure_session_exists(self, session_id: int) -> None:
        session = await self.session_repository.find_by_id_not_deleted(session_id)
        if session is None:
            raise _http_error(
                status.HTTP_404_NOT_FOUND,
                "SESSION_NOT_FOUND",
                "면접 세션을 찾을 수 없습니다.",
            )

    async def get_session_logs(self, session_id: int) -> LlmCallLogListResponse:
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
