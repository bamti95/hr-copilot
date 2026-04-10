from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_active_admin
from models.admin.admin import Admin

from schemas.admin.admin import AdminResponse


from schemas.auth.auth import (
    LoginRequest,
    LogoutRequest,
    MeResponse,
    RefreshTokenRequest,
)

from services.auth.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["인증"])

@router.post("/login", summary="로그인")
async def login(
    request_body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService.login(
        db=db,
        login_id=request_body.login_id,
        password=request_body.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/refresh")
async def refresh_token(
    request_body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService.refresh(
        db=db,
        refresh_token=request_body.refresh_token,
    )


@router.get("/me", response_model=MeResponse)
async def me(
    admin: Admin = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    permissions = await AuthService.get_permissions(db, admin.group_id)
    return MeResponse(
        admin=AdminResponse.from_entity(admin),
        permissions=permissions,
    )


@router.post("/logout")
async def logout(
    request_body: LogoutRequest,
    request: Request,
    admin: Admin = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    await AuthService.logout(
        db=db,
        admin=admin,
        refresh_token=request_body.refresh_token,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return {"message": "로그아웃 되었습니다."}