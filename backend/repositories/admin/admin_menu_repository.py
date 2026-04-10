from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.admin.admin_menu import AdminMenu
from repositories.base_repository import BaseRepository


class AdminMenuRepository(BaseRepository[AdminMenu]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, AdminMenu)    
        
    async def find_by_id(self, menu_id: int) -> AdminMenu | None:
        stmt = select(AdminMenu).where(
            AdminMenu.id == menu_id,
            AdminMenu.del_tf == "N",
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def find_parent_by_id(self, parent_id: int) -> AdminMenu | None:
        stmt = select(AdminMenu).where(
            AdminMenu.id == parent_id,
            AdminMenu.del_tf == "N",
            AdminMenu.use_tf == "Y",
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_menu_key(self, menu_key: str) -> AdminMenu | None:
        stmt = select(AdminMenu).where(
            AdminMenu.menu_key == menu_key,
            AdminMenu.del_tf == "N",
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def find_by_menu_key_excluding_id(
        self,
        menu_key: str,
        menu_id: int,
    ) -> AdminMenu | None:
        stmt = select(AdminMenu).where(
            AdminMenu.menu_key == menu_key,
            AdminMenu.del_tf == "N",
            AdminMenu.id != menu_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def exists_childern(self, menu_id: int) -> bool:
        stmt = select(func.count(AdminMenu.id)).where(
            AdminMenu.parent_id == menu_id,
            AdminMenu.del_tf == "N",
        )
        
        result = await self.db.execute(stmt)
        return result.scalar_one > 0
        
    async def count_list(
        self,
        keyword: str | None = None,
        use_tf: str | None = None,
        parent_id: int | None = None,
    ) -> int:
        conditions = [AdminMenu.del_tf == "N"]

        if keyword:
            like_keyword = f"%{keyword}%"
            conditions.append(
                (AdminMenu.menu_name.ilike(like_keyword)) |
                (AdminMenu.menu_key.ilike(like_keyword))
            )

        if use_tf:
            conditions.append(AdminMenu.use_tf == use_tf)

        if parent_id is not None:
            conditions.append(AdminMenu.parent_id == parent_id)

        stmt = select(func.count(AdminMenu.id)).where(*conditions)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def find_list(
        self,
        page: int,
        size: int,
        keyword: str | None = None,
        use_tf: str | None = None,
        parent_id: int | None = None,
    ) -> list[AdminMenu]:
        conditions = [AdminMenu.del_tf == "N"]

        if keyword:
            like_keyword = f"%{keyword}%"
            conditions.append(
                (AdminMenu.menu_name.ilike(like_keyword)) |
                (AdminMenu.menu_key.ilike(like_keyword))
            )

        if use_tf:
            conditions.append(AdminMenu.use_tf == use_tf)

        if parent_id is not None:
            conditions.append(AdminMenu.parent_id == parent_id)

        stmt = (
            select(AdminMenu)
            .where(*conditions)
            .order_by(AdminMenu.depth.asc(), AdminMenu.sort_no.asc(), AdminMenu.id.asc())
            .offset(page * size)
            .limit(size)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # 트리 조회 : 페이지 기반이 아닌 전체 메뉴 -> service에서 parent-child 구조로 조립 
    async def find_all_for_tree(
        self,
        use_tf: str | None = None,
    ) -> list[AdminMenu]:
        conditions = [AdminMenu.del_tf == "N"]

        if use_tf:
            conditions.append(AdminMenu.use_tf == use_tf)

        stmt = (
            select(AdminMenu)
            .where(*conditions)
            .order_by(AdminMenu.depth.asc(), AdminMenu.sort_no.asc(), AdminMenu.id.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    
    

        
 
    
        
    