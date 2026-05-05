from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.llm_call_log_repository import LlmCallLogRepository
from schemas.llm_usage import (
    LlmUsageCallLog,
    LlmUsageMetric,
    LlmUsageNodeSummary,
    LlmUsageSessionSummary,
    LlmUsageSummaryData,
    LlmUsageSummaryResponse,
)


def _int_value(value: object) -> int:
    return int(value or 0)


def _float_value(value: object) -> float:
    return float(value or 0)


def _decimal_value(value: object) -> Decimal:
    return Decimal(str(value or 0))


class LlmUsageService:
    def __init__(self, db: AsyncSession):
        self.repository = LlmCallLogRepository(db)

    async def get_summary(self, limit: int) -> LlmUsageSummaryResponse:
        metrics_row = await self.repository.get_usage_metrics_row()
        by_node_rows = await self.repository.get_usage_by_node_rows()
        by_session_rows = await self.repository.get_usage_by_session_rows(limit)
        recent_rows = await self.repository.get_recent_usage_rows(limit)

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
