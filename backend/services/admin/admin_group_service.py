from datetime import datetime, timezone
from math import ceil

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.admin.admin_group import AdminGroup
from models.admin.admin_group_menu import AdminGroupMenu
from repositories.admin.admin_group_menu_repository import AdminGroupMenuRepository
from repositories.admin.admin_group_repository import AdminGroupRepository
from repositories.admin.admin_menu_repository import AdminMenuRepository
from schemas.admin.admin_group import (
    AdminGroupListResponse,
    AdminGroupRequest,
    AdminGroupResponse,
)
from schemas.admin.admin_group_menu import AdminGroupMenuPermissionResponse


class AdminGroupService:
    @staticmethod
    async def create_admin_group(
        db: AsyncSession,
        request: AdminGroupRequest,
        actor_login_id: str,
    ) -> AdminGroupResponse:
        repo = AdminGroupRepository(db)
        group_menu_repo = AdminGroupMenuRepository(db)
        menu_repo = AdminMenuRepository(db)

        existing = await repo.find_by_group_name(request.group_name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 groupName 입니다.",
            )

        valid_menu_ids = await AdminGroupService._validate_menu_permissions(
            menu_repo=menu_repo,
            request=request,
        )

        entity = AdminGroup(
            group_name=request.group_name,
            group_desc=request.group_desc,
            use_tf=request.use_tf or "Y",
            del_tf="N",
            reg_adm=actor_login_id,
            reg_date=datetime.now(timezone.utc).replace(tzinfo=None),
        )

        try:
            await repo.add(entity)
            await repo.flush()

            mappings = AdminGroupService._build_group_menu_entities(
                group_id=entity.id,
                request=request,
                actor_login_id=actor_login_id,
                valid_menu_ids=valid_menu_ids,
            )
            if mappings:
                await group_menu_repo.add_all(mappings)

            await db.commit()
            await repo.refresh(entity)

            permission_responses = await AdminGroupService._get_group_permission_responses(
                group_menu_repo=group_menu_repo,
                group_id=entity.id,
            )
            return AdminGroupResponse.from_entity(entity, permission_responses)
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def get_admin_group_list(
        db: AsyncSession,
        page: int,
        size: int,
        keyword: str | None = None,
        use_tf: str | None = None,
    ) -> AdminGroupListResponse:
        repo = AdminGroupRepository(db)

        total_count = await repo.count_list(
            keyword=keyword,
            use_tf=use_tf,
        )
        rows = await repo.find_list(
            page=page,
            size=size,
            keyword=keyword,
            use_tf=use_tf,
        )

        total_pages = ceil(total_count / size) if size > 0 else 1

        return AdminGroupListResponse.of(
            items=[AdminGroupResponse.from_entity(row) for row in rows],
            total_count=total_count,
            total_pages=total_pages,
        )

    @staticmethod
    async def get_admin_group_detail(
        db: AsyncSession,
        admin_group_id: int,
    ) -> AdminGroupResponse:
        repo = AdminGroupRepository(db)
        group_menu_repo = AdminGroupMenuRepository(db)

        entity = await repo.find_by_id(admin_group_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관리자 그룹 정보를 찾을 수 없습니다.",
            )

        permission_responses = await AdminGroupService._get_group_permission_responses(
            group_menu_repo=group_menu_repo,
            group_id=entity.id,
        )
        return AdminGroupResponse.from_entity(entity, permission_responses)

    @staticmethod
    async def update_admin_group(
        db: AsyncSession,
        admin_group_id: int,
        request: AdminGroupRequest,
        actor_login_id: str,
    ) -> AdminGroupResponse:
        repo = AdminGroupRepository(db)
        group_menu_repo = AdminGroupMenuRepository(db)
        menu_repo = AdminMenuRepository(db)

        entity = await repo.find_by_id(admin_group_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관리자 그룹 정보를 찾을 수 없습니다.",
            )

        if request.group_name != entity.group_name:
            duplicate = await repo.find_by_group_name_excluding_id(
                group_name=request.group_name,
                admin_group_id=admin_group_id,
            )
            if duplicate:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="이미 사용 중인 groupName 입니다.",
                )

        valid_menu_ids = await AdminGroupService._validate_menu_permissions(
            menu_repo=menu_repo,
            request=request,
        )

        updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        entity.group_name = request.group_name
        entity.group_desc = request.group_desc
        entity.use_tf = request.use_tf or entity.use_tf
        entity.up_adm = actor_login_id
        entity.up_date = updated_at

        try:
            await group_menu_repo.soft_delete_by_group_id(
                group_id=admin_group_id,
                actor_login_id=actor_login_id,
                deleted_at=updated_at,
            )

            mappings = AdminGroupService._build_group_menu_entities(
                group_id=entity.id,
                request=request,
                actor_login_id=actor_login_id,
                valid_menu_ids=valid_menu_ids,
            )
            if mappings:
                await group_menu_repo.add_all(mappings)

            await db.commit()
            await repo.refresh(entity)

            permission_responses = await AdminGroupService._get_group_permission_responses(
                group_menu_repo=group_menu_repo,
                group_id=entity.id,
            )
            return AdminGroupResponse.from_entity(entity, permission_responses)
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def delete_admin_group(
        db: AsyncSession,
        admin_group_id: int,
        actor_login_id: str,
    ) -> None:
        repo = AdminGroupRepository(db)
        group_menu_repo = AdminGroupMenuRepository(db)

        entity = await repo.find_by_id(admin_group_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관리자 그룹 정보를 찾을 수 없습니다.",
            )

        deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
        entity.del_tf = "Y"
        entity.use_tf = "N"
        entity.del_adm = actor_login_id
        entity.del_date = deleted_at

        try:
            await group_menu_repo.soft_delete_by_group_id(
                group_id=admin_group_id,
                actor_login_id=actor_login_id,
                deleted_at=deleted_at,
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def _validate_menu_permissions(
        menu_repo: AdminMenuRepository,
        request: AdminGroupRequest,
    ) -> set[int]:
        menu_ids = [item.menu_id for item in request.menu_permissions]

        if len(menu_ids) != len(set(menu_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="중복된 menuId 가 포함되어 있습니다.",
            )

        if not menu_ids:
            return set()

        menus = await menu_repo.find_by_ids(menu_ids)
        valid_menu_ids = {menu.id for menu in menus}
        missing_menu_ids = sorted(set(menu_ids) - valid_menu_ids)
        if missing_menu_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"유효하지 않은 menuId 입니다: {missing_menu_ids}",
            )

        return valid_menu_ids

    @staticmethod
    def _build_group_menu_entities(
        group_id: int,
        request: AdminGroupRequest,
        actor_login_id: str,
        valid_menu_ids: set[int],
    ) -> list[AdminGroupMenu]:
        entities: list[AdminGroupMenu] = []
        for item in request.menu_permissions:
            if item.menu_id not in valid_menu_ids:
                continue

            entities.append(
                AdminGroupMenu(
                    group_id=group_id,
                    menu_id=item.menu_id,
                    read_tf=item.read_tf,
                    write_tf=item.write_tf,
                    delete_tf=item.delete_tf,
                    use_tf=item.use_tf,
                    del_tf="N",
                    reg_adm=actor_login_id,
                )
            )
        return entities

    @staticmethod
    async def _get_group_permission_responses(
        group_menu_repo: AdminGroupMenuRepository,
        group_id: int,
    ) -> list[AdminGroupMenuPermissionResponse]:
        rows = await group_menu_repo.find_active_by_group_id(group_id)
        return [
            AdminGroupMenuPermissionResponse.from_entities(group_menu, menu)
            for group_menu, menu in rows
        ]
