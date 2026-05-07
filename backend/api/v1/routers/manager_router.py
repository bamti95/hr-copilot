from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_active_manager, require_role_type
from models.manager import Manager
from schemas.manager import (
    ManagerCreateRequest,
    ManagerListResponse,
    ManagerStatusUpdateRequest,
    ManagerUpdateRequest,
    ManagerResponse
)
from services.manager_service import ManagerService

router = APIRouter(prefix="/managers", tags=["HR 매니저 관리"])


@router.post("", response_model=ManagerResponse, status_code=status.HTTP_201_CREATED)
async def create_manager(
    request_body: ManagerCreateRequest,
    current_manager: Manager = Depends(require_role_type("SYSTEM-MANAGER")),
    db: AsyncSession = Depends(get_db),
) -> ManagerResponse:
    return await ManagerService.create_manager(
        db=db,
        request=request_body,
        actor_id=current_manager.id
        )


@router.get("", response_model=ManagerListResponse)
async def get_managers(
    page: int = Query(0, ge=0),
    size: int = Query(10, ge=1, le=100),
    keyword: str | None = Query(None),
    status_value: str | None = Query(None, alias="status"),
    role_type: str | None = Query(None, alias="roleType"),
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> ManagerListResponse:
    return await ManagerService.get_manager_list(
        db=db,
        page=page,
        size=size,
        keyword=keyword,
        status_value=status_value,
        role_type=role_type,
    )


@router.get("/{manager_id}", response_model=ManagerResponse)
async def get_manager_detail(
    manager_id: int,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> ManagerResponse:
    return await ManagerService.get_manager_detail(db=db, manager_id=manager_id)


@router.put("/{manager_id}", response_model=ManagerResponse)
async def update_manager(
    manager_id: int,
    request_body: ManagerUpdateRequest,
    _: Manager = Depends(require_role_type("SYSTEM-MANAGER")),
    db: AsyncSession = Depends(get_db),
) -> ManagerResponse:
    return await ManagerService.update_manager(db=db, manager_id=manager_id, request=request_body)


@router.patch("/{manager_id}/status", response_model=ManagerResponse)
async def update_manager_status(
    manager_id: int,
    request_body: ManagerStatusUpdateRequest,
    _: Manager = Depends(require_role_type("SYSTEM-MANAGER")),
    db: AsyncSession = Depends(get_db),
) -> ManagerResponse:
    return await ManagerService.update_manager_status(
        db=db,
        manager_id=manager_id,
        status_value=request_body.status,
    )


@router.delete("/{manager_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_manager(
    manager_id: int,
    current_manager: Manager = Depends(require_role_type("SYSTEM-MANAGER")),
    db: AsyncSession = Depends(get_db),
) -> Response:
    await ManagerService.delete_manager(db=db, manager_id=manager_id, actor_id=current_manager.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
