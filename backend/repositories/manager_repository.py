from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.manager import Manager
from repositories.base_repository import BaseRepository


class ManagerRepository(BaseRepository[Manager]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Manager)

    async def find_by_login_id(self, login_id: str) -> Manager | None:
        stmt = select(Manager).where(
            Manager.login_id == login_id,
            Manager.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_login_id_excluding_id(self, login_id: str, manager_id: int) -> Manager | None:
        stmt = select(Manager).where(
            Manager.login_id == login_id,
            Manager.deleted_at.is_(None),
            Manager.id != manager_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_id_not_deleted(self, manager_id: int) -> Manager | None:
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
