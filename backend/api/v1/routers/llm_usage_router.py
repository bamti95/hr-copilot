from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_active_manager
from models.manager import Manager
from schemas.llm_usage import LlmUsageSummaryResponse
from services.llm_usage_service import LlmUsageService

router = APIRouter(prefix="/llm-usage", tags=["llm-usage"])


@router.get("/summary", response_model=LlmUsageSummaryResponse)
async def get_llm_usage_summary(
    limit: int = Query(20, ge=1, le=100),
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> LlmUsageSummaryResponse:
    service = LlmUsageService(db)
    return await service.get_summary(limit)
