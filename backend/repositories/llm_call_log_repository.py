from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.llm_call_log import LlmCallLog
from repositories.base_repository import BaseRepository


class LlmCallLogRepository(BaseRepository[LlmCallLog]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, LlmCallLog)

    async def find_by_session_id(self, session_id: int) -> list[LlmCallLog]:
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
