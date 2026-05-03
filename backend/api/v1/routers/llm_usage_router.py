from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_active_manager
from models.candidate import Candidate
from models.interview_session import InterviewSession
from models.llm_call_log import LlmCallLog
from models.manager import Manager
from schemas.llm_usage import (
    LlmUsageCallLog,
    LlmUsageMetric,
    LlmUsageNodeSummary,
    LlmUsageSessionSummary,
    LlmUsageSummaryData,
    LlmUsageSummaryResponse,
)

router = APIRouter(prefix="/llm-usage", tags=["llm-usage"])


def _int_value(value: object) -> int:
    return int(value or 0)


def _float_value(value: object) -> float:
    return float(value or 0)


def _decimal_value(value: object) -> Decimal:
    return Decimal(str(value or 0))


@router.get("/summary", response_model=LlmUsageSummaryResponse)
async def get_llm_usage_summary(
    limit: int = Query(20, ge=1, le=100),
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> LlmUsageSummaryResponse:
    failed_call = case((LlmCallLog.call_status != "success", 1), else_=0)

    metrics_row = (
        await db.execute(
            select(
                func.count(LlmCallLog.id),
                func.coalesce(func.sum(LlmCallLog.input_tokens), 0),
                func.coalesce(func.sum(LlmCallLog.output_tokens), 0),
                func.coalesce(func.sum(LlmCallLog.total_tokens), 0),
                func.coalesce(func.sum(LlmCallLog.estimated_cost), 0),
                func.coalesce(func.avg(LlmCallLog.elapsed_ms), 0),
                func.coalesce(func.sum(failed_call), 0),
            )
        )
    ).one()

    by_node_rows = (
        await db.execute(
            select(
                func.coalesce(LlmCallLog.node_name, "unknown").label("node_name"),
                func.count(LlmCallLog.id),
                func.coalesce(func.sum(LlmCallLog.input_tokens), 0),
                func.coalesce(func.sum(LlmCallLog.output_tokens), 0),
                func.coalesce(func.sum(LlmCallLog.total_tokens), 0),
                func.coalesce(func.sum(LlmCallLog.estimated_cost), 0),
                func.coalesce(func.avg(LlmCallLog.elapsed_ms), 0),
                func.coalesce(func.sum(failed_call), 0),
            )
            .group_by(LlmCallLog.node_name)
            .order_by(desc(func.coalesce(func.sum(LlmCallLog.estimated_cost), 0)))
        )
    ).all()

    by_session_rows = (
        await db.execute(
            select(
                LlmCallLog.interview_sessions_id,
                LlmCallLog.candidate_id,
                Candidate.name,
                InterviewSession.target_job,
                func.count(LlmCallLog.id),
                func.coalesce(func.sum(LlmCallLog.total_tokens), 0),
                func.coalesce(func.sum(LlmCallLog.estimated_cost), 0),
                func.coalesce(func.avg(LlmCallLog.elapsed_ms), 0),
                func.max(LlmCallLog.created_at),
            )
            .join(Candidate, Candidate.id == LlmCallLog.candidate_id)
            .join(InterviewSession, InterviewSession.id == LlmCallLog.interview_sessions_id)
            .group_by(
                LlmCallLog.interview_sessions_id,
                LlmCallLog.candidate_id,
                Candidate.name,
                InterviewSession.target_job,
            )
            .order_by(desc(func.max(LlmCallLog.created_at)))
            .limit(limit)
        )
    ).all()

    recent_rows = (
        await db.execute(
            select(LlmCallLog, Candidate.name)
            .join(Candidate, Candidate.id == LlmCallLog.candidate_id)
            .order_by(desc(LlmCallLog.created_at))
            .limit(limit)
        )
    ).all()

    return LlmUsageSummaryResponse(
        data=LlmUsageSummaryData(
            metrics=LlmUsageMetric(
                total_calls=_int_value(metrics_row[0]),
                total_input_tokens=_int_value(metrics_row[1]),
                total_output_tokens=_int_value(metrics_row[2]),
                total_tokens=_int_value(metrics_row[3]),
                estimated_cost=_decimal_value(metrics_row[4]),
                avg_elapsed_ms=_float_value(metrics_row[5]),
                failed_calls=_int_value(metrics_row[6]),
            ),
            by_node=[
                LlmUsageNodeSummary(
                    node_name=row[0],
                    call_count=_int_value(row[1]),
                    input_tokens=_int_value(row[2]),
                    output_tokens=_int_value(row[3]),
                    total_tokens=_int_value(row[4]),
                    estimated_cost=_decimal_value(row[5]),
                    avg_elapsed_ms=_float_value(row[6]),
                    failed_calls=_int_value(row[7]),
                )
                for row in by_node_rows
            ],
            by_session=[
                LlmUsageSessionSummary(
                    session_id=row[0],
                    candidate_id=row[1],
                    candidate_name=row[2],
                    target_job=row[3],
                    call_count=_int_value(row[4]),
                    total_tokens=_int_value(row[5]),
                    estimated_cost=_decimal_value(row[6]),
                    avg_elapsed_ms=_float_value(row[7]),
                    last_called_at=row[8],
                )
                for row in by_session_rows
            ],
            recent_calls=[
                LlmUsageCallLog(
                    id=log.id,
                    manager_id=log.manager_id,
                    session_id=log.interview_sessions_id,
                    candidate_id=log.candidate_id,
                    candidate_name=candidate_name,
                    node_name=log.node_name,
                    model_name=log.model_name,
                    input_tokens=log.input_tokens,
                    output_tokens=log.output_tokens,
                    total_tokens=log.total_tokens,
                    estimated_cost=log.estimated_cost,
                    currency=log.currency,
                    elapsed_ms=log.elapsed_ms,
                    call_status=log.call_status,
                    error_message=log.error_message,
                    created_at=log.created_at,
                )
                for log, candidate_name in recent_rows
            ],
        ),
        message="LLM 사용량 요약 조회 성공",
    )
