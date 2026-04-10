from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.admin import Admin
from repositories.base_repository import BaseRepository


class AdminRepository(BaseRepository[Admin]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Admin)

    async def find_by_login_id(self, login_id: str) -> Admin | None:
        stmt = select(Admin).where(
            Admin.login_id == login_id,
            Admin.del_tf == "N",
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_login_id_excluding_id(
        self,
        login_id: str,
        admin_id: int,
    ) -> Admin | None:
        stmt = select(Admin).where(
            Admin.login_id == login_id,
            Admin.del_tf == "N",
            Admin.id != admin_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_id_not_deleted(self, admin_id: int) -> Admin | None:
        stmt = select(Admin).where(
            Admin.id == admin_id,
            Admin.del_tf == "N",
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def count_list(
        self,
        keyword: str | None = None,
        status: str | None = None,
        use_tf: str | None = None,
    ) -> int:
        conditions = [Admin.del_tf == "N"]

        if keyword:
            like_keyword = f"%{keyword}%"
            conditions.append(
                or_(
                    Admin.login_id.ilike(like_keyword),
                    Admin.name.ilike(like_keyword),
                    Admin.email.ilike(like_keyword),
                )
            )

        if status:
            conditions.append(Admin.status == status)

        if use_tf:
            conditions.append(Admin.use_tf == use_tf)

        stmt = select(func.count(Admin.id)).where(*conditions)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def find_list(
        self,
        page: int,
        size: int,
        keyword: str | None = None,
        status: str | None = None,
        use_tf: str | None = None,
    ) -> list[Admin]:
        conditions = [Admin.del_tf == "N"]

        if keyword:
            like_keyword = f"%{keyword}%"
            conditions.append(
                or_(
                    Admin.login_id.ilike(like_keyword),
                    Admin.name.ilike(like_keyword),
                    Admin.email.ilike(like_keyword),
                )
            )

        if status:
            conditions.append(Admin.status == status)

        if use_tf:
            conditions.append(Admin.use_tf == use_tf)

        stmt = (
            select(Admin)
            .where(*conditions)
            .order_by(Admin.id.desc())
            .offset(page * size)
            .limit(size)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())