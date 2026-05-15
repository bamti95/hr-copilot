"""LLM 사용량 요약 데이터를 조합한다.

원시 로그를 그대로 노출하지 않고,
메트릭, 노드별 집계, 세션별 집계, 최근 호출 내역으로 나눠
대시보드에서 바로 쓸 수 있는 형태로 변환한다.
"""

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
    """집계 결과의 null 값을 0으로 보정해 정수로 변환한다."""
    return int(value or 0)


def _float_value(value: object) -> float:
    """평균 시간 같은 수치를 안전하게 실수로 변환한다."""
    return float(value or 0)


def _decimal_value(value: object) -> Decimal:
    """비용 합계를 부동소수 오차 없이 Decimal로 변환한다."""
    return Decimal(str(value or 0))


def _build_interview_summary(row) -> LlmUsageSessionSummary:
    """면접 질문 생성 파이프라인 집계 행을 응답 스키마로 바꾼다."""
    return LlmUsageSessionSummary(
        session_id=row[0],
        candidate_id=row[1],
        candidate_name=row[2],
        target_job=row[3],
        pipeline_type="INTERVIEW_QUESTION",
        target_type="INTERVIEW_SESSION",
        target_id=row[0],
        call_count=_int_value(row[4]),
        total_tokens=_int_value(row[5]),
        estimated_cost=_decimal_value(row[6]),
        avg_elapsed_ms=_float_value(row[7]),
        last_called_at=row[8],
    )


def _build_job_posting_summary(row) -> LlmUsageSessionSummary:
    """채용공고 분석 파이프라인 집계 행을 응답 스키마로 바꾼다."""
    return LlmUsageSessionSummary(
        session_id=None,
        candidate_id=None,
        candidate_name=None,
        target_job=row[5],
        pipeline_type=row[0],
        target_type=row[1],
        target_id=row[2],
        job_posting_id=row[3],
        job_posting_analysis_report_id=row[4],
        job_title=row[5],
        risk_level=row[6],
        call_count=_int_value(row[7]),
        total_tokens=_int_value(row[8]),
        estimated_cost=_decimal_value(row[9]),
        avg_elapsed_ms=_float_value(row[10]),
        last_called_at=row[11],
    )


class LlmUsageService:
    """LLM 사용량 대시보드용 집계 서비스다."""

    def __init__(self, db: AsyncSession):
        self.repository = LlmCallLogRepository(db)

    async def get_summary(
        self,
        limit: int,
        pipeline_type: str | None = "INTERVIEW_QUESTION",
    ) -> LlmUsageSummaryResponse:
        """파이프라인 유형별 사용량 요약을 한 번에 구성한다.

        조회 기준은 pipeline_type 하나로 통일한다.
        이렇게 해야 메트릭, 세션, 최근 호출이 같은 범위를 보게 된다.
        """
        metrics_row = await self.repository.get_usage_metrics_row(pipeline_type)
        by_node_rows = await self.repository.get_usage_by_node_rows(pipeline_type)
        by_session_rows = await self.repository.get_usage_by_session_rows(
            limit,
            pipeline_type,
        )
        recent_rows = await self.repository.get_recent_usage_rows(limit, pipeline_type)

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
                    _build_job_posting_summary(row)
                    if pipeline_type == "JOB_POSTING_COMPLIANCE"
                    else _build_interview_summary(row)
                    for row in by_session_rows
                ],
                recent_calls=[
                    LlmUsageCallLog(
                        id=log.id,
                        manager_id=log.manager_id,
                        session_id=log.interview_sessions_id,
                        candidate_id=log.candidate_id,
                        candidate_name=candidate_name,
                        pipeline_type=log.pipeline_type,
                        target_type=log.target_type,
                        target_id=log.target_id,
                        job_posting_id=log.job_posting_id,
                        job_posting_analysis_report_id=log.job_posting_analysis_report_id,
                        job_title=job_title,
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
                    for log, candidate_name, job_title in recent_rows
                ],
            ),
            message="LLM usage summary fetched successfully.",
        )
