from sqlalchemy import case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.candidate import Candidate
from models.interview_session import InterviewSession
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

    async def get_usage_metrics_row(self):
        failed_call = case((LlmCallLog.call_status != "success", 1), else_=0)
        result = await self.db.execute(
            select(
                func.count(LlmCallLog.id),
                func.coalesce(func.sum(LlmCallLog.input_tokens), 0),
                func.coalesce(func.sum(LlmCallLog.output_tokens), 0),
                func.coalesce(func.sum(LlmCallLog.total_tokens), 0),
                func.coalesce(func.sum(LlmCallLog.estimated_cost), 0),
                func.coalesce(func.avg(LlmCallLog.elapsed_ms), 0),
                func.coalesce(func.sum(failed_call), 0),
            )
        )
        return result.one()

    async def get_usage_by_node_rows(self):
        failed_call = case((LlmCallLog.call_status != "success", 1), else_=0)
        result = await self.db.execute(
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
        return result.all()

    async def get_usage_by_session_rows(self, limit: int):
        result = await self.db.execute(
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
        return result.all()

    async def get_recent_usage_rows(self, limit: int):
        result = await self.db.execute(
            select(LlmCallLog, Candidate.name)
            .join(Candidate, Candidate.id == LlmCallLog.candidate_id)
            .order_by(desc(LlmCallLog.created_at))
            .limit(limit)
        )
        return result.all()
