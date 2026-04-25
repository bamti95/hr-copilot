from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.interview_question import InterviewQuestion
from repositories.base_repository import BaseRepository


class InterviewQuestionRepository(BaseRepository[InterviewQuestion]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, InterviewQuestion)

    async def soft_delete_by_session_id(
        self,
        session_id: int,
        actor_id: int | None,
    ) -> None:
        stmt = select(InterviewQuestion).where(
            InterviewQuestion.interview_sessions_id == session_id,
            InterviewQuestion.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        now = datetime.now(timezone.utc)
        for question in result.scalars().all():
            question.deleted_at = now
            question.deleted_by = actor_id

    async def find_active_by_session_id(
        self,
        session_id: int,
    ) -> list[InterviewQuestion]:
        stmt = (
            select(InterviewQuestion)
            .where(
                InterviewQuestion.interview_sessions_id == session_id,
                InterviewQuestion.deleted_at.is_(None),
            )
            .order_by(InterviewQuestion.id.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
