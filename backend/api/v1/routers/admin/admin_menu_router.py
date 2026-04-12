from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import require_menu_permission
from models.admin.admin import Admin
from schemas.admin.admin_menu import (
    AdmMenuListResponse,
    AdminMenuRequest,
    AdminMenuResponse,
)
from schemas.admin.admin_menu_tree import AdmMenuTreeResponse
from services.admin.admin_menu_service import AdminMenuService

router = APIRouter(prefix="/admin-menus", tags=["관리자 메뉴"])


@router.post("", response_model=AdminMenuResponse, status_code=status.HTTP_201_CREATED)
async def create_admin_menu(
    request: AdminMenuRequest,
    current_admin: Admin = Depends(require_menu_permission("admin", "write")),
    db: AsyncSession = Depends(get_db),
):
    return await AdminMenuService.create_admin_menu(
        db=db,
        request=request,
        actor_login_id=current_admin.login_id,
    )


@router.get("", response_model=AdmMenuListResponse)
async def get_admin_menu_list(
    page: int = Query(0, ge=0),
    size: int = Query(10, ge=1, le=100),
    keyword: str | None = Query(None),
    use_tf: str | None = Query(None, alias="useTf"),
    parent_id: int | None = Query(None, alias="parentId"),
    _: Admin = Depends(require_menu_permission("admin", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await AdminMenuService.get_admin_menu_list(
        db=db,
        page=page,
        size=size,
        keyword=keyword,
        use_tf=use_tf,
        parent_id=parent_id,
    )


@router.get("/tree", response_model=list[AdmMenuTreeResponse])
async def get_admin_menu_tree(
    use_tf: str | None = Query(None, alias="useTf"),
    _: Admin = Depends(require_menu_permission("admin", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await AdminMenuService.get_admin_menu_tree(
        db=db,
        use_tf=use_tf,
    )


@router.get("/{menu_id}", response_model=AdminMenuResponse)
async def get_admin_menu_detail(
    menu_id: int,
    _: Admin = Depends(require_menu_permission("admin", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await AdminMenuService.get_admin_menu_detail(
        db=db,
        menu_id=menu_id,
    )


@router.put("/{menu_id}", response_model=AdminMenuResponse)
async def update_admin_menu(
    menu_id: int,
    request: AdminMenuRequest,
    current_admin: Admin = Depends(require_menu_permission("admin", "write")),
    db: AsyncSession = Depends(get_db),
):
    return await AdminMenuService.update_admin_menu(
        db=db,
        menu_id=menu_id,
        request=request,
        actor_login_id=current_admin.login_id,
    )


@router.delete("/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin_menu(
    menu_id: int,
    current_admin: Admin = Depends(require_menu_permission("admin", "delete")),
    db: AsyncSession = Depends(get_db),
):
    await AdminMenuService.delete_admin_menu(
        db=db,
        menu_id=menu_id,
        actor_login_id=current_admin.login_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
