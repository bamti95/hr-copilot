from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.candidate import Candidate
from models.interview_session import InterviewSession
from repositories.base_repository import BaseRepository


class SessionRepository(BaseRepository[InterviewSession]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, InterviewSession)

    @staticmethod
    def _base_join_stmt():
        return (
            select(
                InterviewSession,
                Candidate.name.label("candidate_name"),
            )
            .join(
                Candidate,
                InterviewSession.candidate_id == Candidate.id,
            )
            .where(
                InterviewSession.deleted_at.is_(None),
                Candidate.deleted_at.is_(None),
            )
        )

    @staticmethod
    def _apply_filters(stmt, candidate_id: int | None, target_job: str | None):
        if candidate_id is not None:
            stmt = stmt.where(InterviewSession.candidate_id == candidate_id)
        if target_job and target_job.strip():
            stmt = stmt.where(InterviewSession.target_job.ilike(f"%{target_job.strip()}%"))
        return stmt

    async def find_by_id_not_deleted(self, session_id: int) -> InterviewSession | None:
        stmt = select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_id_any(self, session_id: int) -> InterviewSession | None:
        stmt = select(InterviewSession).where(InterviewSession.id == session_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_question_generation_queued(
        self,
        session: InterviewSession,
    ) -> None:
        session.question_generation_status = "QUEUED"
        session.question_generation_error = None
        session.question_generation_requested_at = datetime.now(timezone.utc)
        session.question_generation_completed_at = None

    async def mark_question_generation_processing(
        self,
        session: InterviewSession,
    ) -> None:
        session.question_generation_status = "PROCESSING"
        session.question_generation_error = None

    async def mark_question_generation_completed(
        self,
        session: InterviewSession,
        status: str,
        error: str | None = None,
    ) -> None:
        session.question_generation_status = status
        session.question_generation_error = error
        session.question_generation_completed_at = datetime.now(timezone.utc)

    async def get_detail_with_candidate(self, session_id: int) -> InterviewSession | None:
        stmt = self._base_join_stmt().where(InterviewSession.id == session_id)
        result = await self.db.execute(stmt)
        row = result.one_or_none()
        if row is None:
            return None

        session, candidate_name = row
        setattr(session, "candidate_name", candidate_name)
        return session

    async def count_list(
        self,
        candidate_id: int | None = None,
        target_job: str | None = None,
    ) -> int:
        stmt = (
            select(func.count(InterviewSession.id))
            .select_from(InterviewSession)
            .join(Candidate, InterviewSession.candidate_id == Candidate.id)
            .where(
                InterviewSession.deleted_at.is_(None),
                Candidate.deleted_at.is_(None),
            )
        )
        stmt = self._apply_filters(stmt, candidate_id, target_job)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def find_list(
        self,
        page: int,
        limit: int,
        candidate_id: int | None = None,
        target_job: str | None = None,
    ) -> list[InterviewSession]:
        offset = (page - 1) * limit
        stmt = self._base_join_stmt().order_by(InterviewSession.id.desc()).offset(offset).limit(limit)
        stmt = self._apply_filters(stmt, candidate_id, target_job)
        result = await self.db.execute(stmt)

        sessions: list[InterviewSession] = []
        for session, candidate_name in result.all():
            setattr(session, "candidate_name", candidate_name)
            sessions.append(session)
        return sessions
