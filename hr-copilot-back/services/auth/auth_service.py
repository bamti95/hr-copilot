from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.config import settings
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
    verify_password,
)
from models.admin.admin import Admin
from models.admin.admin_access_log import AdminAccessLog
from models.admin.admin_group_menu import AdminGroupMenu
from models.admin.admin_refresh_token import AdminRefreshToken
from models.admin.admin_menu import AdminMenu
from schemas.admin.admin import AdminResponse 
from schemas.auth.auth import MenuPermissionResponse, TokenPairResponse

class AuthService:
    @staticmethod
    async def login(
        db: AsyncSession,
        login_id: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenPairResponse:
        if len(password.encode('utf-8')) > 72:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="아이디 또는 비밀번호가 올바르지 않습니다.", # 보안상 상세 사유는 숨김
            )
        
        stmt = (
            select(Admin)
            .options(selectinload(Admin.group))
            .where(
                Admin.login_id == login_id,
                Admin.del_tf == "N",
                Admin.use_tf == "Y",
            )
        )
        result = await db.execute(stmt)
        admin = result.scalar_one_or_none()

        if not admin or not verify_password(password, admin.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="아이디 또는 비밀번호가 올바르지 않습니다.",
            )

        if admin.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="비활성화된 관리자 계정입니다.",
            )

        admin.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)

        access_token = create_access_token(
            subject=str(admin.id),
            extra={
                "loginId": admin.login_id,
                "groupId": admin.group_id,
                "name": admin.name,
            },
        )
        refresh_token = create_refresh_token(subject=str(admin.id))

        refresh_row = AdminRefreshToken(
            admin_id=admin.id,
            token_hash=hash_token(refresh_token),
            expires_at=(
                datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            ).replace(tzinfo=None),
            revoked_tf="N",
            reg_adm=admin.login_id,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        db.add(refresh_row)

        db.add(
            AdminAccessLog(
                admin_id=admin.id,
                action_type="LOGIN",
                action_target="auth",
                ip_address=ip_address,
                user_agent=user_agent,
                result_tf="Y",
                message="로그인 성공",
            )
        )

        await db.commit()

        permissions = await AuthService.get_permissions(db, admin.group_id)

        return TokenPairResponse(
            accessToken=access_token,
            refreshToken=refresh_token,
            tokenType="Bearer",
            admin=AdminResponse.from_entity(admin),
            permissions=permissions,
        )

    @staticmethod
    async def refresh(
        db: AsyncSession,
        refresh_token: str,
    ):
        try:
            payload = decode_token(refresh_token)
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 refresh token 입니다.",
            )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="refresh token 타입이 아닙니다.",
            )

        admin_id = int(payload["sub"])
        hashed = hash_token(refresh_token)

        stmt = select(AdminRefreshToken).where(
            AdminRefreshToken.admin_id == admin_id,
            AdminRefreshToken.token_hash == hashed,
            AdminRefreshToken.revoked_tf == "N",
        )
        result = await db.execute(stmt)
        token_row = result.scalar_one_or_none()

        if not token_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="저장된 refresh token 이 없습니다.",
            )

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if token_row.expires_at < now:
            token_row.revoked_tf = "Y"
            token_row.up_date = now
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="refresh token 이 만료되었습니다.",
            )

        admin_stmt = select(Admin).where(
            Admin.id == admin_id,
            Admin.del_tf == "N",
            Admin.use_tf == "Y",
            Admin.status == "ACTIVE",
        )
        admin_result = await db.execute(admin_stmt)
        admin = admin_result.scalar_one_or_none()

        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="관리자 계정을 찾을 수 없습니다.",
            )

        token_row.revoked_tf = "Y"
        token_row.up_adm = admin.login_id
        token_row.up_date = now

        new_access_token = create_access_token(
            subject=str(admin.id),
            extra={
                "loginId": admin.login_id,
                "groupId": admin.group_id,
                "name": admin.name,
            },
        )
        new_refresh_token = create_refresh_token(subject=str(admin.id))

        new_refresh_row = AdminRefreshToken(
            admin_id=admin.id,
            token_hash=hash_token(new_refresh_token),
            expires_at=(
                datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            ).replace(tzinfo=None),
            revoked_tf="N",
            reg_adm=admin.login_id,
        )
        db.add(new_refresh_row)
        await db.commit()

        return {
            "accessToken": new_access_token,
            "refreshToken": new_refresh_token,
            "tokenType": "Bearer",
        }

    @staticmethod
    async def logout(
        db: AsyncSession,
        admin: Admin,
        refresh_token: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        if refresh_token:
            hashed = hash_token(refresh_token)
            stmt = select(AdminRefreshToken).where(
                AdminRefreshToken.admin_id == admin.id,
                AdminRefreshToken.token_hash == hashed,
                AdminRefreshToken.revoked_tf == "N",
            )
            result = await db.execute(stmt)
            token_row = result.scalar_one_or_none()
            if token_row:
                token_row.revoked_tf = "Y"
                token_row.up_adm = admin.login_id
                token_row.up_date = datetime.now(timezone.utc).replace(tzinfo=None)

        db.add(
            AdminAccessLog(
                admin_id=admin.id,
                action_type="LOGOUT",
                action_target="auth",
                ip_address=ip_address,
                user_agent=user_agent,
                result_tf="Y",
                message="로그아웃",
            )
        )
        await db.commit()

    @staticmethod
    async def get_permissions(
        db: AsyncSession,
        group_id: int,
    ) -> list[MenuPermissionResponse]:
        stmt = (
            select(AdminGroupMenu, AdminMenu)
            .join(AdminMenu, AdminGroupMenu.menu_id == AdminMenu.id)
            .where(
                AdminGroupMenu.group_id == group_id,
                AdminGroupMenu.del_tf == "N",
                AdminGroupMenu.use_tf == "Y",
                AdminMenu.del_tf == "N",
                AdminMenu.use_tf == "Y",
            )
            .order_by(AdminMenu.depth.asc(), AdminMenu.sort_no.asc(), AdminMenu.id.asc())
        )
        result = await db.execute(stmt)

        items: list[MenuPermissionResponse] = []
        for group_menu, menu in result.all():
            items.append(
                MenuPermissionResponse(
                    menuId=menu.id,
                    menuKey=menu.menu_key,
                    menuName=menu.menu_name,
                    menuPath=menu.menu_path,
                    readTf=group_menu.read_tf,
                    writeTf=group_menu.write_tf,
                    deleteTf=group_menu.delete_tf,
                )
            )
        return items