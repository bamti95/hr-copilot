from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_active_manager
from models.manager import Manager
from schemas.llm_usage import LlmUsageSummaryResponse
from services.llm_usage_service import LlmUsageService

router = APIRouter(prefix="/llm-usage", tags=["AI 사용량 관리"])


@router.get("/summary",
            response_model=LlmUsageSummaryResponse,
            summary="HR 매니저 대시보드 요약 조회")
async def get_llm_usage_summary(
    limit: int = Query(20, ge=1, le=100),
    pipeline_type: str | None = Query("INTERVIEW_QUESTION", alias="pipelineType"),
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> LlmUsageSummaryResponse:
    service = LlmUsageService(db)
    return await service.get_summary(limit, pipeline_type=pipeline_type)
