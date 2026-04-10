from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import (
    get_current_active_admin,
    require_menu_permission,
)
from models.admin.admin import Admin

from schemas.admin.admin import (
    AdminListResponse,
    AdminRequest,
    AdminResponse,
)

from services.admin.admin_service import AdminService

router = APIRouter(prefix="/admins", tags=["관리자"])

# 관리자 목록 조회
@router.get("", response_model=AdminListResponse)
async def get_admins(
    page: int = Query(0, ge=0),
    size: int = Query(10, ge=1, le=100),
    keyword: str | None = Query(None),
    status_param: str | None = Query(None, alias="status"),
    use_tf: str | None = Query(None, alias="useTf"),
    _: Admin = Depends(require_menu_permission("admin", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await AdminService.get_admin_list(
        db=db,
        page=page,
        size=size,
        keyword=keyword,
        status=status_param,
        use_tf=use_tf,
    )


# 관리자 상세 조회
@router.get("/{admin_id}", response_model=AdminResponse)
async def get_admin_detail(
    admin_id: int,
    _: Admin = Depends(require_menu_permission("admin", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await AdminService.get_admin_detail(db, admin_id)


# 관리자 등록
@router.post("", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(
    request_body: AdminRequest,
    current_admin: Admin = Depends(require_menu_permission("admin", "write")),
    db: AsyncSession = Depends(get_db),
):
    return await AdminService.create_admin(
        db=db,
        request=request_body,
        actor_login_id=current_admin.login_id,
    )


# 관리자 수정
@router.put("/{admin_id}", response_model=AdminResponse)
async def update_admin(
    admin_id: int,
    request_body: AdminRequest,
    current_admin: Admin = Depends(require_menu_permission("admin", "write")),
    db: AsyncSession = Depends(get_db),
):
    return await AdminService.update_admin(
        db=db,
        admin_id=admin_id,
        request=request_body,
        actor_login_id=current_admin.login_id,
    )


# 관리자 삭제 (soft delete)
@router.delete("/{admin_id}")
async def delete_admin(
    admin_id: int,
    current_admin: Admin = Depends(require_menu_permission("admin", "delete")),
    db: AsyncSession = Depends(get_db),
):
    await AdminService.delete_admin(
        db=db,
        admin_id=admin_id,
        actor_login_id=current_admin.login_id,
    )
    return {"message": "삭제되었습니다."}