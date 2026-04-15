from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_active_manager
from models.manager import Manager
from schemas.auth.auth import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
)
from services.auth.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse, summary="관리자 로그인")
async def login(
    request_body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    return await AuthService.login(
        db=db,
        login_id=request_body.login_id,
        password=request_body.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/refresh", response_model=RefreshTokenResponse, summary="토큰 재발급")
async def refresh_token(
    request_body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> RefreshTokenResponse:
    return await AuthService.refresh(
        db=db,
        refresh_token=request_body.refresh_token,
    )


@router.post("/logout", summary="로그아웃")
async def logout(
    request_body: LogoutRequest,
    manager: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
):
    await AuthService.logout(
        db=db,
        manager=manager,
        refresh_token=request_body.refresh_token,
    )
    return {"message": "로그아웃되었습니다."}
