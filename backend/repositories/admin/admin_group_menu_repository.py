from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.admin.admin_group_menu import AdminGroupMenu
from models.admin.admin_menu import AdminMenu
from repositories.base_repository import BaseRepository


class AdminGroupMenuRepository(BaseRepository[AdminGroupMenu]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, AdminGroupMenu)

    async def add_all(self, entities: list[AdminGroupMenu]) -> None:
        self.db.add_all(entities)

    async def find_active_by_group_id(
        self,
        group_id: int,
    ) -> list[tuple[AdminGroupMenu, AdminMenu]]:
        stmt = (
            select(AdminGroupMenu, AdminMenu)
            .join(AdminMenu, AdminGroupMenu.menu_id == AdminMenu.id)
            .where(
                AdminGroupMenu.group_id == group_id,
                AdminGroupMenu.del_tf == "N",
                AdminMenu.del_tf == "N",
            )
            .order_by(AdminMenu.depth.asc(), AdminMenu.sort_no.asc(), AdminMenu.id.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.all())

    async def soft_delete_by_group_id(
        self,
        group_id: int,
        actor_login_id: str,
        deleted_at: datetime,
    ) -> None:
        stmt = select(AdminGroupMenu).where(
            AdminGroupMenu.group_id == group_id,
            AdminGroupMenu.del_tf == "N",
        )
        result = await self.db.execute(stmt)
        rows = list(result.scalars().all())

        for row in rows:
            row.del_tf = "Y"
            row.use_tf = "N"
            row.del_adm = actor_login_id
            row.del_date = deleted_at

    async def soft_delete_by_menu_id(
        self,
        menu_id: int,
        actor_login_id: str,
        deleted_at: datetime,
    ) -> None:
        stmt = select(AdminGroupMenu).where(
            AdminGroupMenu.menu_id == menu_id,
            AdminGroupMenu.del_tf == "N",
        )
        result = await self.db.execute(stmt)
        rows = list(result.scalars().all())

        for row in rows:
            row.del_tf = "Y"
            row.use_tf = "N"
            row.del_adm = actor_login_id
            row.del_date = deleted_at
