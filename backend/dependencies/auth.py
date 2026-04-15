import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import decode_token
from models.manager import Manager

bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_manager(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Manager:
    token = credentials.credentials

    try:
        payload = decode_token(token)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 access token 입니다.",
        ) from exc

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="access token 타입이 아닙니다.",
        )

    manager_id = int(payload["sub"])
    stmt = select(Manager).where(
        Manager.id == manager_id,
        Manager.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    manager = result.scalar_one_or_none()

    if not manager:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="관리자 계정을 찾을 수 없습니다.",
        )

    return manager


async def get_current_active_manager(
    manager: Manager = Depends(get_current_manager),
) -> Manager:
    if manager.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 관리자 계정입니다.",
        )
    return manager


def require_role_type(role_type: str):
    async def dependency(
        manager: Manager = Depends(get_current_active_manager),
    ) -> Manager:
        if manager.role_type != role_type:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="해당 기능에 접근할 권한이 없습니다.",
            )
        return manager

    return dependency
