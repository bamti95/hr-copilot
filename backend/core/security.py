"""비밀번호 해시와 JWT 발급/검증을 담당한다."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException
import jwt
from passlib.context import CryptContext

from core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__truncate_error=False)


def hash_password(password: str) -> str:
    """평문 비밀번호를 bcrypt 해시로 변환한다."""
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """입력 비밀번호와 저장된 해시가 일치하는지 확인한다."""
    if not password or not password_hash:
        return False

    try:
        return pwd_context.verify(password, password_hash)
    except ValueError:
        # 72바이트 초과 등으로 인한 에러 발생 시 False 반환
        return False


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    """Access token을 발급한다."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "exp": expire,
    }
    if extra:
        payload.update(extra)

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """Refresh token을 발급한다."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": subject,
        "type": "refresh",
        "jti": secrets.token_hex(16),
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """JWT를 검증하고 payload를 반환한다."""
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        # 여기서 바로 에러를 던지거나, 호출부에서 처리하도록 설계
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def hash_token(token: str) -> str:
    """토큰 원문을 저장하지 않기 위해 SHA-256 해시로 변환한다."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
