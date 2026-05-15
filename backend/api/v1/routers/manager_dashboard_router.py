"""관리자 대시보드 API 라우터다."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_active_manager
from models.manager import Manager
from schemas.manager_dashboard import ManagerDashboardSummaryResponse
from services.manager_dashboard_service import ManagerDashboardService

router = APIRouter(prefix="/manager/dashboard", tags=["HR 매니저 대시보드 요약"])


@router.get("/summary", response_model=ManagerDashboardSummaryResponse, summary="매니저 대시보드 요약")
async def get_manager_dashboard_summary(
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> ManagerDashboardSummaryResponse:
    service = ManagerDashboardService(db)
    return await service.get_summary()

