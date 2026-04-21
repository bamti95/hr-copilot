from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.prompt_profile import PromptProfile
from repositories.base_repository import BaseRepository


class PromptProfileRepository(BaseRepository[PromptProfile]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, PromptProfile)

    async def find_by_id_active(self, profile_id: int) -> PromptProfile | None:
        stmt = select(PromptProfile).where(
            PromptProfile.id == profile_id,
            PromptProfile.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_id_any(self, profile_id: int) -> PromptProfile | None:
        stmt = select(PromptProfile).where(PromptProfile.id == profile_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_active_by_profile_key(self, profile_key: str) -> PromptProfile | None:
        stmt = select(PromptProfile).where(
            PromptProfile.profile_key == profile_key.strip(),
            PromptProfile.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def _list_conditions(self, search: str | None, target_job: str | None = None) -> list:
        conditions = [PromptProfile.deleted_at.is_(None)]
        if search and search.strip():
            term = f"%{search.strip()}%"
            conditions.append(
                or_(
                    PromptProfile.profile_key.ilike(term),
                    PromptProfile.system_prompt.ilike(term),
                )
            )
        if target_job and target_job.strip():
            conditions.append(PromptProfile.target_job == target_job.strip())
        return conditions

    async def count_list(self, search: str | None = None, target_job: str | None = None) -> int:
        conditions = self._list_conditions(search, target_job)
        stmt = select(func.count(PromptProfile.id)).where(*conditions)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def find_list(
        self,
        page: int,
        limit: int,
        search: str | None = None,
        target_job: str | None = None,
    ) -> list[PromptProfile]:
        conditions = self._list_conditions(search, target_job)
        offset = (page - 1) * limit
        stmt = (
            select(PromptProfile)
            .where(*conditions)
            .order_by(PromptProfile.id.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
