"""면접 질문 리포지토리.

세션별 질문 목록을 관리하고, 삭제는 물리 삭제 대신 soft delete로 처리한다.
질문 생성 파이프라인과 관리자 화면에서 함께 사용한다.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.interview_question import InterviewQuestion
from repositories.base_repository import BaseRepository


class InterviewQuestionRepository(BaseRepository[InterviewQuestion]):
    """면접 질문 엔터티 조회와 soft delete를 담당한다."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, InterviewQuestion)

    async def soft_delete_by_session_id(
        self,
        session_id: int,
        actor_id: int | None,
    ) -> None:
        """세션에 속한 질문을 모두 soft delete 처리한다.

        복구 가능성과 이력 보존을 위해 레코드를 지우지 않는다.
        """
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
        """삭제되지 않은 질문만 순서대로 조회한다."""
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
