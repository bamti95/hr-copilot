"""관리자 계정 조회 리포지토리.

로그인 ID 중복 확인과 관리자 목록 검색을 담당한다.
운영 화면에서 자주 쓰는 검색 조건을 공통 방식으로 묶어 둔다.
"""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.manager import Manager
from repositories.base_repository import BaseRepository


class ManagerRepository(BaseRepository[Manager]):
    """관리자 엔터티 조회와 목록 검색을 담당한다."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Manager)

    async def find_by_login_id(self, login_id: str) -> Manager | None:
        """삭제되지 않은 로그인 ID 기준 관리자 1건을 조회한다."""
        stmt = select(Manager).where(
            Manager.login_id == login_id,
            Manager.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_login_id_excluding_id(self, login_id: str, manager_id: int) -> Manager | None:
        """자기 자신을 제외한 로그인 ID 중복 관리자를 찾는다."""
        stmt = select(Manager).where(
            Manager.login_id == login_id,
            Manager.deleted_at.is_(None),
            Manager.id != manager_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_id_not_deleted(self, manager_id: int) -> Manager | None:
        """삭제되지 않은 관리자 1건을 조회한다."""
        stmt = select(Manager).where(
            Manager.id == manager_id,
            Manager.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def count_list(
        self,
        keyword: str | None = None,
        status: str | None = None,
        role_type: str | None = None,
    ) -> int:
        """검색 조건에 맞는 관리자 수를 계산한다."""
        conditions = [Manager.deleted_at.is_(None)]

        if keyword:
            like_keyword = f"%{keyword}%"
            conditions.append(
                or_(
                    Manager.login_id.ilike(like_keyword),
                    Manager.name.ilike(like_keyword),
                    Manager.email.ilike(like_keyword),
                )
            )

        if status:
            conditions.append(Manager.status == status)

        if role_type:
            conditions.append(Manager.role_type == role_type)

        stmt = select(func.count(Manager.id)).where(*conditions)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def find_list(
        self,
        page: int,
        size: int,
        keyword: str | None = None,
        status: str | None = None,
        role_type: str | None = None,
    ) -> list[Manager]:
        """관리자 목록을 최신 ID 순으로 페이지 조회한다."""
        conditions = [Manager.deleted_at.is_(None)]

        if keyword:
            like_keyword = f"%{keyword}%"
            conditions.append(
                or_(
                    Manager.login_id.ilike(like_keyword),
                    Manager.name.ilike(like_keyword),
                    Manager.email.ilike(like_keyword),
                )
            )

        if status:
            conditions.append(Manager.status == status)

        if role_type:
            conditions.append(Manager.role_type == role_type)

        stmt = (
            select(Manager)
            .where(*conditions)
            .order_by(Manager.id.desc())
            .offset(page * size)
            .limit(size)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
