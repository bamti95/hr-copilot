from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class LlmCallLogResponse(BaseModel):
    id: int

    manager_id: int | None = Field(None, alias="managerId")
    candidate_id: int = Field(..., alias="candidateId")
    document_id: int | None = Field(None, alias="documentId")
    prompt_profile_id: int | None = Field(None, alias="promptProfileId")
    interview_sessions_id: int = Field(..., alias="interviewSessionsId")

    model_name: str = Field(..., alias="modelName")
    node_name: str | None = Field(None, alias="nodeName")

    run_id: str | None = Field(None, alias="runId")
    parent_run_id: str | None = Field(None, alias="parentRunId")
    trace_id: str | None = Field(None, alias="traceId")
    run_type: str | None = Field(None, alias="runType")
    execution_order: int | None = Field(None, alias="executionOrder")

    request_json: dict | None = Field(None, alias="requestJson")
    output_json: dict | None = Field(None, alias="outputJson")
    response_json: dict | None = Field(None, alias="responseJson")

    input_tokens: int = Field(..., alias="inputTokens")
    output_tokens: int = Field(..., alias="outputTokens")
    total_tokens: int = Field(..., alias="totalTokens")

    estimated_cost: Decimal = Field(..., alias="estimatedCost")
    currency: str
    elapsed_ms: int | None = Field(None, alias="elapsedMs")
    cost_amount: Decimal | None = Field(None, alias="costAmount")

    call_status: str = Field(..., alias="callStatus")
    error_message: str | None = Field(None, alias="errorMessage")
    call_time: int = Field(..., alias="callTime")

    started_at: datetime | None = Field(None, alias="startedAt")
    ended_at: datetime | None = Field(None, alias="endedAt")
    created_at: datetime = Field(..., alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @staticmethod
    def from_entity(entity: object) -> "LlmCallLogResponse":
        return LlmCallLogResponse.model_validate(entity)


class LlmCallLogListResponse(BaseModel):
    session_id: int = Field(..., alias="sessionId")
    trace_id: str | None = Field(None, alias="traceId")
    items: list[LlmCallLogResponse]

    model_config = ConfigDict(populate_by_name=True)

    @staticmethod
    def of(
        *,
        session_id: int,
        items: list[LlmCallLogResponse],
    ) -> "LlmCallLogListResponse":
        trace_id = items[0].trace_id if items else None
        return LlmCallLogListResponse(
            sessionId=session_id,
            traceId=trace_id,
            items=items,
        )
