"""채용공고 분석 단계별 추적 로그를 기록하는 서비스다."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from models.llm_call_log import LlmCallLog


class JobPostingTraceRecorder:
    def __init__(
        self,
        *,
        db: AsyncSession,
        manager_id: int | None,
        job_posting_id: int,
        report_id: int,
    ) -> None:
        self.db = db
        self.manager_id = manager_id
        self.job_posting_id = job_posting_id
        self.report_id = report_id
        self.trace_id = str(uuid.uuid4())
        self.root_run_id = str(uuid.uuid4())
        self.execution_order = 0

    async def record(
        self,
        *,
        node_name: str,
        request_json: dict[str, Any] | None = None,
        output_json: dict[str, Any] | None = None,
        response_json: dict[str, Any] | None = None,
        call_status: str = "success",
        error_message: str | None = None,
        elapsed_ms: int = 0,
        model_name: str = "local-pipeline",
        run_type: str = "chain",
    ) -> None:
        self.execution_order += 1
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        self.db.add(
            LlmCallLog(
                manager_id=self.manager_id,
                pipeline_type="JOB_POSTING_COMPLIANCE",
                target_type="JOB_POSTING_ANALYSIS_REPORT",
                target_id=self.report_id,
                job_posting_id=self.job_posting_id,
                job_posting_analysis_report_id=self.report_id,
                model_name=model_name,
                node_name=node_name,
                run_id=str(uuid.uuid4()),
                parent_run_id=self.root_run_id,
                trace_id=self.trace_id,
                run_type=run_type,
                execution_order=self.execution_order,
                request_json=request_json,
                output_json=output_json,
                response_json=response_json,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                estimated_cost=Decimal("0"),
                currency="USD",
                elapsed_ms=elapsed_ms,
                call_status=call_status,
                error_message=error_message,
                cost_amount=Decimal("0"),
                call_time=elapsed_ms,
                started_at=now,
                ended_at=now,
            )
        )


async def record_timed_node(
    recorder: JobPostingTraceRecorder,
    *,
    node_name: str,
    request_json: dict[str, Any] | None,
    output_json: dict[str, Any] | None,
    elapsed_started_at: float,
    model_name: str = "local-pipeline",
) -> None:
    await recorder.record(
        node_name=node_name,
        request_json=request_json,
        output_json=output_json,
        elapsed_ms=int((time.perf_counter() - elapsed_started_at) * 1000),
        model_name=model_name,
    )

