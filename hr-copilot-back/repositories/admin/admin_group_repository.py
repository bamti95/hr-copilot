from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.admin.admin_group import AdminGroup
from repositories.base_repository import BaseRepository


class AdminGroupRepository(BaseRepository[AdminGroup]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, AdminGroup)

    async def find_by_id(self, admin_group_id: int) -> AdminGroup | None:
        stmt = select(AdminGroup).where(
            AdminGroup.id == admin_group_id,
            AdminGroup.del_tf == "N",
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_group_name(self, group_name: str) -> AdminGroup | None:
        stmt = select(AdminGroup).where(
            AdminGroup.group_name == group_name,
            AdminGroup.del_tf == "N",
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_group_name_excluding_id(
        self,
        group_name: str,
        admin_group_id: int,
    ) -> AdminGroup | None:
        stmt = select(AdminGroup).where(
            AdminGroup.group_name == group_name,
            AdminGroup.del_tf == "N",
            AdminGroup.id != admin_group_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def count_list(
        self,
        keyword: str | None = None,
        use_tf: str | None = None,
    ) -> int:
        conditions = [AdminGroup.del_tf == "N"]

        if keyword:
            conditions.append(AdminGroup.group_name.ilike(f"%{keyword}%"))

        if use_tf:
            conditions.append(AdminGroup.use_tf == use_tf)

        stmt = select(func.count(AdminGroup.id)).where(*conditions)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def find_list(
        self,
        page: int,
        size: int,
        keyword: str | None = None,
        use_tf: str | None = None,
    ) -> list[AdminGroup]:
        conditions = [AdminGroup.del_tf == "N"]

        if keyword:
            conditions.append(AdminGroup.group_name.ilike(f"%{keyword}%"))

        if use_tf:
            conditions.append(AdminGroup.use_tf == use_tf)

        stmt = (
            select(AdminGroup)
            .where(*conditions)
            .order_by(AdminGroup.id.desc())
            .offset(page * size)
            .limit(size)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())