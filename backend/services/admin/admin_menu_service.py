from datetime import datetime, timezone
from math import ceil

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.admin.admin_menu import AdminMenu
from repositories.admin.admin_group_menu_repository import AdminGroupMenuRepository
from repositories.admin.admin_menu_repository import AdminMenuRepository
from schemas.admin.admin_menu import (
    AdmMenuListResponse,
    AdminMenuRequest,
    AdminMenuResponse,
)
from schemas.admin.admin_menu_tree import AdmMenuTreeResponse


class AdminMenuService:
    @staticmethod
    async def create_admin_menu(
        db: AsyncSession,
        request: AdminMenuRequest,
        actor_login_id: str,
    ) -> AdminMenuResponse:
        repo = AdminMenuRepository(db)

        duplicate = await repo.find_by_menu_key(request.menu_key)
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 menuKey 입니다.",
            )

        depth = 1
        if request.parent_id is not None:
            parent = await repo.find_parent_by_id(request.parent_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="유효한 상위 메뉴를 찾을 수 없습니다.",
                )
            depth = parent.depth + 1

        entity = AdminMenu(
            parent_id=request.parent_id,
            menu_name=request.menu_name,
            menu_key=request.menu_key,
            menu_path=request.menu_path,
            depth=depth,
            sort_no=request.sort_no,
            icon=request.icon,
            use_tf=request.use_tf or "Y",
            del_tf="N",
            reg_adm=actor_login_id,
        )

        try:
            await repo.add(entity)
            await db.commit()
            await repo.refresh(entity)
            return AdminMenuResponse.from_entity(entity)
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def get_admin_menu_list(
        db: AsyncSession,
        page: int,
        size: int,
        keyword: str | None = None,
        use_tf: str | None = None,
        parent_id: int | None = None,
    ) -> AdmMenuListResponse:
        repo = AdminMenuRepository(db)

        total_count = await repo.count_list(
            keyword=keyword,
            use_tf=use_tf,
            parent_id=parent_id,
        )
        rows = await repo.find_list(
            page=page,
            size=size,
            keyword=keyword,
            use_tf=use_tf,
            parent_id=parent_id,
        )

        total_pages = ceil(total_count / size) if size > 0 else 1
        return AdmMenuListResponse.of(
            items=[AdminMenuResponse.from_entity(row) for row in rows],
            total_count=total_count,
            total_pages=total_pages,
        )

    @staticmethod
    async def get_admin_menu_detail(
        db: AsyncSession,
        menu_id: int,
    ) -> AdminMenuResponse:
        repo = AdminMenuRepository(db)

        entity = await repo.find_by_id(menu_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관리자 메뉴 정보를 찾을 수 없습니다.",
            )

        return AdminMenuResponse.from_entity(entity)

    @staticmethod
    async def get_admin_menu_tree(
        db: AsyncSession,
        use_tf: str | None = None,
    ) -> list[AdmMenuTreeResponse]:
        repo = AdminMenuRepository(db)
        rows = await repo.find_all_for_tree(use_tf=use_tf)

        children_by_parent: dict[int | None, list[AdminMenu]] = {}
        for row in rows:
            children_by_parent.setdefault(row.parent_id, []).append(row)

        def build(parent_id: int | None) -> list[AdmMenuTreeResponse]:
            nodes = children_by_parent.get(parent_id, [])
            return [
                AdmMenuTreeResponse.from_entity(node, children=build(node.id))
                for node in nodes
            ]

        return build(None)

    @staticmethod
    async def update_admin_menu(
        db: AsyncSession,
        menu_id: int,
        request: AdminMenuRequest,
        actor_login_id: str,
    ) -> AdminMenuResponse:
        repo = AdminMenuRepository(db)
        entity = await repo.find_by_id(menu_id)

        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관리자 메뉴 정보를 찾을 수 없습니다.",
            )

        if request.menu_key != entity.menu_key:
            duplicate = await repo.find_by_menu_key_excluding_id(request.menu_key, menu_id)
            if duplicate:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="이미 사용 중인 menuKey 입니다.",
                )

        depth = 1
        previous_depth = entity.depth
        if request.parent_id is not None:
            if request.parent_id == menu_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="자기 자신을 상위 메뉴로 지정할 수 없습니다.",
                )

            parent = await repo.find_parent_by_id(request.parent_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="유효한 상위 메뉴를 찾을 수 없습니다.",
                )

            current_parent = parent
            while current_parent is not None:
                if current_parent.id == menu_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="하위 메뉴를 상위 메뉴로 지정할 수 없습니다.",
                    )
                if current_parent.parent_id is None:
                    break
                current_parent = await repo.find_by_id(current_parent.parent_id)

            depth = parent.depth + 1

        entity.parent_id = request.parent_id
        entity.menu_name = request.menu_name
        entity.menu_key = request.menu_key
        entity.menu_path = request.menu_path
        entity.depth = depth
        entity.sort_no = request.sort_no
        entity.icon = request.icon
        entity.use_tf = request.use_tf or entity.use_tf
        entity.up_adm = actor_login_id
        entity.up_date = datetime.now(timezone.utc).replace(tzinfo=None)

        try:
            if previous_depth != depth:
                await AdminMenuService._update_descendant_depths(
                    repo=repo,
                    root_menu_id=menu_id,
                    root_depth=depth,
                )
            await db.commit()
            await repo.refresh(entity)
            return AdminMenuResponse.from_entity(entity)
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def delete_admin_menu(
        db: AsyncSession,
        menu_id: int,
        actor_login_id: str,
    ) -> None:
        repo = AdminMenuRepository(db)
        group_menu_repo = AdminGroupMenuRepository(db)

        entity = await repo.find_by_id(menu_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관리자 메뉴 정보를 찾을 수 없습니다.",
            )

        has_children = await repo.exists_children(menu_id)
        if has_children:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="하위 메뉴가 있는 경우 삭제할 수 없습니다.",
            )

        deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
        entity.del_tf = "Y"
        entity.use_tf = "N"
        entity.del_adm = actor_login_id
        entity.del_date = deleted_at

        try:
            await group_menu_repo.soft_delete_by_menu_id(
                menu_id=menu_id,
                actor_login_id=actor_login_id,
                deleted_at=deleted_at,
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def _update_descendant_depths(
        repo: AdminMenuRepository,
        root_menu_id: int,
        root_depth: int,
    ) -> None:
        rows = await repo.find_all_for_tree()
        children_by_parent: dict[int | None, list[AdminMenu]] = {}
        for row in rows:
            children_by_parent.setdefault(row.parent_id, []).append(row)

        def apply_depth(parent_id: int, parent_depth: int) -> None:
            for child in children_by_parent.get(parent_id, []):
                child.depth = parent_depth + 1
                apply_depth(child.id, child.depth)

        apply_depth(root_menu_id, root_depth)
