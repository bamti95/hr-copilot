"""애플리케이션과 DB 상태를 점검하는 헬스체크 라우터다."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
async def health_check():
    """애플리케이션 프로세스가 응답 가능한지 확인한다."""
    return {"status": "ok"}


@router.get("/db")
async def health_check_db(db: AsyncSession = Depends(get_db)):
    """DB 연결이 실제로 가능한지 확인한다."""
    result = await db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "database": "connected",
        "result": result.scalar_one(),
    }
