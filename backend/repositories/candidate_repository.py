from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.candidate import Candidate
from repositories.base_repository import BaseRepository


class CandidateRepository(BaseRepository[Candidate]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Candidate)

    async def find_by_id_not_deleted(self, candidate_id: int) -> Candidate | None:
        stmt = select(Candidate).where(
            Candidate.id == candidate_id,
            Candidate.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_id_any(self, candidate_id: int) -> Candidate | None:
        stmt = select(Candidate).where(Candidate.id == candidate_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_active_by_email(self, email: str) -> Candidate | None:
        stmt = select(Candidate).where(
            func.lower(Candidate.email) == email.strip().lower(),
            Candidate.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_active_by_email_excluding_id(self, email: str, exclude_id: int) -> Candidate | None:
        stmt = select(Candidate).where(
            func.lower(Candidate.email) == email.strip().lower(),
            Candidate.deleted_at.is_(None),
            Candidate.id != exclude_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def _list_conditions(
        self,
        apply_status: str | None,
        search: str | None,
    ) -> list:
        conditions = [Candidate.deleted_at.is_(None)]
        if apply_status:
            conditions.append(Candidate.apply_status == apply_status)
        if search and search.strip():
            term = f"%{search.strip()}%"
            conditions.append(
                or_(
                    Candidate.name.ilike(term),
                    Candidate.email.ilike(term),
                )
            )
        return conditions

    async def count_list(
        self,
        apply_status: str | None = None,
        search: str | None = None,
    ) -> int:
        conditions = self._list_conditions(apply_status, search)
        stmt = select(func.count(Candidate.id)).where(*conditions)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def find_list(
        self,
        page: int,
        limit: int,
        apply_status: str | None = None,
        search: str | None = None,
    ) -> list[Candidate]:
        conditions = self._list_conditions(apply_status, search)
        offset = (page - 1) * limit
        stmt = (
            select(Candidate)
            .where(*conditions)
            .order_by(Candidate.id.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
