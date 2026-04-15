from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
    verify_password,
)
from models.manager import Manager
from models.manager_refresh_token import ManagerRefreshToken
from schemas.auth.auth import LoginResponse, RefreshTokenResponse
from schemas.manager import ManagerResponse


class AuthService:
    @staticmethod
    async def login(
        db: AsyncSession,
        login_id: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> LoginResponse:
        if len(password.encode("utf-8")) > 72:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="아이디 또는 비밀번호가 올바르지 않습니다.",
            )

        stmt = select(Manager).where(
            Manager.login_id == login_id,
            Manager.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        manager = result.scalar_one_or_none()

        if not manager or not verify_password(password, manager.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="아이디 또는 비밀번호가 올바르지 않습니다.",
            )

        if manager.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="비활성화된 관리자 계정입니다.",
            )

        now = datetime.now(timezone.utc)
        manager.last_login_at = now

        access_token = create_access_token(
            subject=str(manager.id),
            extra={
                "loginId": manager.login_id,
                "name": manager.name,
                "roleType": manager.role_type,
            },
        )
        refresh_token = create_refresh_token(subject=str(manager.id))

        db.add(
            ManagerRefreshToken(
                manager_id=manager.id,
                token_hash=hash_token(refresh_token),
                expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
                revoked_tf="N",
                user_agent=user_agent,
                ip_address=ip_address,
                created_by=manager.id,
            )
        )

        await db.commit()
        await db.refresh(manager)

        return LoginResponse(
            accessToken=access_token,
            refreshToken=refresh_token,
            tokenType="Bearer",
            manager=ManagerResponse.from_entity(manager),
        )

    @staticmethod
    async def refresh(
        db: AsyncSession,
        refresh_token: str,
    ) -> RefreshTokenResponse:
        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="refresh token 타입이 아닙니다.",
            )

        manager_id = int(payload["sub"])
        hashed_token = hash_token(refresh_token)

        stmt = select(ManagerRefreshToken).where(
            ManagerRefreshToken.manager_id == manager_id,
            ManagerRefreshToken.token_hash == hashed_token,
            ManagerRefreshToken.revoked_tf == "N",
            ManagerRefreshToken.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        token_row = result.scalar_one_or_none()

        if not token_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효한 refresh token 이 없습니다.",
            )

        now = datetime.now(timezone.utc)
        if token_row.expires_at < now:
            token_row.revoked_tf = "Y"
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="refresh token 이 만료되었습니다.",
            )

        manager_stmt = select(Manager).where(
            Manager.id == manager_id,
            Manager.deleted_at.is_(None),
        )
        manager_result = await db.execute(manager_stmt)
        manager = manager_result.scalar_one_or_none()

        if not manager or manager.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="관리자 계정을 찾을 수 없거나 비활성 상태입니다.",
            )

        token_row.revoked_tf = "Y"

        new_access_token = create_access_token(
            subject=str(manager.id),
            extra={
                "loginId": manager.login_id,
                "name": manager.name,
                "roleType": manager.role_type,
            },
        )
        new_refresh_token = create_refresh_token(subject=str(manager.id))

        db.add(
            ManagerRefreshToken(
                manager_id=manager.id,
                token_hash=hash_token(new_refresh_token),
                expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
                revoked_tf="N",
                created_by=manager.id,
            )
        )
        await db.commit()

        return RefreshTokenResponse(
            accessToken=new_access_token,
            refreshToken=new_refresh_token,
            tokenType="Bearer",
        )

    @staticmethod
    async def logout(
        db: AsyncSession,
        manager: Manager,
        refresh_token: str | None = None,
    ) -> None:
        if not refresh_token:
            return

        hashed_token = hash_token(refresh_token)
        stmt = select(ManagerRefreshToken).where(
            ManagerRefreshToken.manager_id == manager.id,
            ManagerRefreshToken.token_hash == hashed_token,
            ManagerRefreshToken.revoked_tf == "N",
            ManagerRefreshToken.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        token_row = result.scalar_one_or_none()

        if token_row:
            token_row.revoked_tf = "Y"
            await db.commit()
