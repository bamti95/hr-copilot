from datetime import datetime, timezone
from math import ceil

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.admin.admin_group import AdminGroup
from repositories.admin.admin_group_repository import AdminGroupRepository
from schemas.admin.admin_group import (
    AdminGroupListResponse,
    AdminGroupRequest,
    AdminGroupResponse,
)

class AdminGroupService:
    @staticmethod
    async def create_admin_group(
        db: AsyncSession,
        request: AdminGroupRequest,
        actor_login_id: str,
    ) -> AdminGroupResponse:
        repo = AdminGroupRepository(db)

        existing = await repo.find_by_group_name(request.group_name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 groupName 입니다.",
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
            await db.commit()
            await repo.refresh(entity)
            return AdminGroupResponse.from_entity(entity)
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

        entity = await repo.find_by_id(admin_group_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관리자 그룹 정보를 찾을 수 없습니다.",
            )

        return AdminGroupResponse.from_entity(entity)

    @staticmethod
    async def update_admin_group(
        db: AsyncSession,
        admin_group_id: int,
        request: AdminGroupRequest,
        actor_login_id: str,
    ) -> AdminGroupResponse:
        repo = AdminGroupRepository(db)

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

        entity.group_name = request.group_name
        entity.group_desc = request.group_desc
        entity.use_tf = request.use_tf or entity.use_tf
        entity.up_adm = actor_login_id
        entity.up_date = datetime.now(timezone.utc).replace(tzinfo=None)

        try:
            await db.commit()
            await repo.refresh(entity)
            return AdminGroupResponse.from_entity(entity)
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

        entity = await repo.find_by_id(admin_group_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관리자 그룹 정보를 찾을 수 없습니다.",
            )

        entity.del_tf = "Y"
        entity.del_adm = actor_login_id
        entity.del_date = datetime.now(timezone.utc).replace(tzinfo=None)

        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise