from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import require_menu_permission
from models.admin.admin import Admin
from schemas.admin.admin_group import (
    AdminGroupListResponse,
    AdminGroupRequest,
    AdminGroupResponse,
)
from services.admin.admin_group_service import AdminGroupService

router = APIRouter(prefix="/admin-groups", tags=["관리자 그룹"])


@router.post("", response_model=AdminGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_admin_group(
    request: AdminGroupRequest,
    current_admin: Admin = Depends(require_menu_permission("admin", "write")),
    db: AsyncSession = Depends(get_db),
):
    return await AdminGroupService.create_admin_group(
        db=db,
        request=request,
        actor_login_id=current_admin.login_id,
    )


@router.get("", response_model=AdminGroupListResponse)
async def get_admin_group_list(
    page: int = Query(0, ge=0),
    size: int = Query(10, ge=1, le=100),
    keyword: str | None = Query(None),
    use_tf: str | None = Query(None, alias="useTf"),
    _: Admin = Depends(require_menu_permission("admin", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await AdminGroupService.get_admin_group_list(
        db=db,
        page=page,
        size=size,
        keyword=keyword,
        use_tf=use_tf,
    )


@router.get("/{admin_group_id}", response_model=AdminGroupResponse)
async def get_admin_group_detail(
    admin_group_id: int,
    _: Admin = Depends(require_menu_permission("admin", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await AdminGroupService.get_admin_group_detail(
        db=db,
        admin_group_id=admin_group_id,
    )


@router.put("/{admin_group_id}", response_model=AdminGroupResponse)
async def update_admin_group(
    admin_group_id: int,
    request: AdminGroupRequest,
    current_admin: Admin = Depends(require_menu_permission("admin", "write")),
    db: AsyncSession = Depends(get_db),
):
    return await AdminGroupService.update_admin_group(
        db=db,
        admin_group_id=admin_group_id,
        request=request,
        actor_login_id=current_admin.login_id,
    )


@router.delete("/{admin_group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin_group(
    admin_group_id: int,
    current_admin: Admin = Depends(require_menu_permission("admin", "delete")),
    db: AsyncSession = Depends(get_db),
):
    await AdminGroupService.delete_admin_group(
        db=db,
        admin_group_id=admin_group_id,
        actor_login_id=current_admin.login_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
