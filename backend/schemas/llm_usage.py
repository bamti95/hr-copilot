from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class LlmUsageMetric(BaseModel):
    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: Decimal = Decimal("0")
    avg_elapsed_ms: float = 0
    failed_calls: int = 0


class LlmUsageNodeSummary(BaseModel):
    node_name: str
    call_count: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: Decimal
    avg_elapsed_ms: float
    failed_calls: int


class LlmUsageSessionSummary(BaseModel):
    session_id: int
    candidate_id: int
    candidate_name: str
    target_job: str
    call_count: int
    total_tokens: int
    estimated_cost: Decimal
    avg_elapsed_ms: float
    last_called_at: datetime | None = None


class LlmUsageCallLog(BaseModel):
    id: int
    manager_id: int | None = None
    session_id: int
    candidate_id: int
    candidate_name: str
    node_name: str | None = None
    model_name: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: Decimal
    currency: str
    elapsed_ms: int | None = None
    call_status: str
    error_message: str | None = None
    created_at: datetime


class LlmUsageSummaryData(BaseModel):
    metrics: LlmUsageMetric
    by_node: list[LlmUsageNodeSummary] = Field(default_factory=list)
    by_session: list[LlmUsageSessionSummary] = Field(default_factory=list)
    recent_calls: list[LlmUsageCallLog] = Field(default_factory=list)


class LlmUsageSummaryResponse(BaseModel):
    success: bool = True
    data: LlmUsageSummaryData
    message: str
