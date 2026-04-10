from typing import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.admin.admin import Admin

from core.database import get_db
from core.security import decode_token
from services.auth.auth_service import AuthService

bearer_scheme = HTTPBearer(auto_error=True)

async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Admin:
    token = credentials.credentials

    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 access token 입니다.",
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="access token 타입이 아닙니다.",
        )

    admin_id = int(payload["sub"])

    stmt = select(Admin).where(
        Admin.id == admin_id,
        Admin.del_tf == "N",
        Admin.use_tf == "Y",
    )
    result = await db.execute(stmt)
    admin = result.scalar_one_or_none()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="관리자 계정을 찾을 수 없습니다.",
        )

    return admin


async def get_current_active_admin(
    admin: Admin = Depends(get_current_admin),
) -> Admin:
    if admin.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 관리자 계정입니다.",
        )
    return admin


def require_menu_permission(menu_key: str, action: str) -> Callable:
    async def dependency(
        admin: Admin = Depends(get_current_active_admin),
        db: AsyncSession = Depends(get_db),
    ) -> Admin:
        permissions = await AuthService.get_permissions(db, admin.group_id)

        matched = next((p for p in permissions if p.menu_key == menu_key), None)
        if not matched:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="해당 메뉴 접근 권한이 없습니다.",
            )

        allowed = False
        if action == "read":
            allowed = matched.read_tf == "Y"
        elif action == "write":
            allowed = matched.write_tf == "Y"
        elif action == "delete":
            allowed = matched.delete_tf == "Y"

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{menu_key} 메뉴에 대한 {action} 권한이 없습니다.",
            )

        return admin

    return dependency