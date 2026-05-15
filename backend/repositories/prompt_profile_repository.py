"""프롬프트 프로필 조회 리포지토리.

직무별 프롬프트 프로필을 조회하고, 관리자 화면용 목록 검색을 제공한다.
생성자 이름을 함께 붙여 화면에서 바로 쓸 수 있게 만드는 것이 특징이다.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.manager import Manager
from models.prompt_profile import PromptProfile
from repositories.base_repository import BaseRepository


class PromptProfileRepository(BaseRepository[PromptProfile]):
    """프롬프트 프로필 조회와 목록 검색을 담당한다."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, PromptProfile)

    async def find_by_id_active(self, profile_id: int) -> PromptProfile | None:
        """활성 프로필 1건을 생성자 이름과 함께 조회한다."""
        stmt = (
            select(PromptProfile, Manager.name.label("created_name"))
            .outerjoin(Manager, PromptProfile.created_by == Manager.id)
            .where(
                PromptProfile.id == profile_id,
                PromptProfile.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        row = result.one_or_none()
        if row is None:
            return None
        profile, created_name = row
        setattr(profile, "created_name", created_name)
        return profile

    async def find_by_id_any(self, profile_id: int) -> PromptProfile | None:
        """삭제 여부와 관계없이 프로필 1건을 조회한다."""
        stmt = select(PromptProfile).where(PromptProfile.id == profile_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_active_by_profile_key(self, profile_key: str) -> PromptProfile | None:
        """프로필 키 기준 활성 프로필을 조회한다."""
        stmt = select(PromptProfile).where(
            PromptProfile.profile_key == profile_key.strip(),
            PromptProfile.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def _list_conditions(self, search: str | None, target_job: str | None = None) -> list:
        """목록 조회 공통 조건을 만든다."""
        conditions = [PromptProfile.deleted_at.is_(None)]
        if search and search.strip():
            term = f"%{search.strip()}%"
            conditions.append(PromptProfile.profile_key.ilike(term))
        if target_job and target_job.strip():
            conditions.append(PromptProfile.target_job == target_job.strip())
        return conditions

    async def count_list(self, search: str | None = None, target_job: str | None = None) -> int:
        """검색 조건에 맞는 프로필 수를 센다."""
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
        """프로필 목록을 생성자 이름과 함께 페이지 조회한다."""
        conditions = self._list_conditions(search, target_job)
        offset = (page - 1) * limit
        stmt = (
            select(PromptProfile, Manager.name.label("created_name"))
            .outerjoin(Manager, PromptProfile.created_by == Manager.id)
            .where(*conditions)
            .order_by(PromptProfile.id.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        profiles: list[PromptProfile] = []
        for profile, created_name in result.all():
            setattr(profile, "created_name", created_name)
            profiles.append(profile)
        return profiles
