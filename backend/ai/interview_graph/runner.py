import logging
import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from ai.graph_usage import collect_llm_usage_update
from ai.interview_graph.nodes import (
    analyzer_node,
    build_state_node,
    driller_node,
    final_formatter_node,
    increment_retry_for_driller_node,
    increment_retry_for_questioner_node,
    predictor_node,
    questioner_node,
    reviewer_node,
    scorer_node,
    selector_lite_node,
    selector_node,
)
from ai.interview_graph.router import route_after_scoring
from ai.interview_graph.schemas import DocumentAnalysisOutput, QuestionGenerationResponse
from ai.interview_graph.state import AgentState
from core.database import AsyncSessionLocal
from models.llm_call_log import LlmCallLog
from schemas.session_generation import CandidateInterviewPrepInput

logger = logging.getLogger(__name__)


def _jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, str | int | float | bool):
        return value
    return str(value)


def build_node_execution_log(
    *,
    node_name: str,
    node_update: Any,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "node": node_name,
        "model_name": "local",
        "run_type": "chain",
        "request_json": {"node": node_name},
        "output_json": _jsonable(node_update),
        "response_json": None,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "estimated_cost": 0,
        "call_status": "success",
        "elapsed_ms": None,
        "started_at": now,
        "ended_at": now,
    }


def _as_naive_datetime(value: Any) -> datetime | None:
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


async def save_llm_call_logs(
    *,
    payload: CandidateInterviewPrepInput,
    usages: list[dict[str, Any]],
) -> None:
    if not usages:
        return

    prompt_profile_id = payload.prompt_profile.id if payload.prompt_profile else None
    trace_id = str(uuid.uuid4())
    root_run_id = str(uuid.uuid4())
    async with AsyncSessionLocal() as db:
        try:
            for execution_order, usage in enumerate(usages, start=1):
                elapsed_ms = usage.get("elapsed_ms")
                estimated_cost = Decimal(str(usage.get("estimated_cost", 0) or 0))
                db.add(
                    LlmCallLog(
                        manager_id=payload.session.manager_id,
                        candidate_id=payload.candidate.candidate_id,
                        document_id=None,
                        prompt_profile_id=prompt_profile_id,
                        interview_sessions_id=payload.session.session_id,
                        pipeline_type="INTERVIEW_QUESTION",
                        target_type="INTERVIEW_SESSION",
                        target_id=payload.session.session_id,
                        model_name=usage.get("model_name") or "unknown",
                        node_name=usage.get("node"),
                        run_id=usage.get("run_id") or str(uuid.uuid4()),
                        parent_run_id=usage.get("parent_run_id") or root_run_id,
                        trace_id=usage.get("trace_id") or trace_id,
                        run_type=usage.get("run_type") or "chain",
                        execution_order=usage.get("execution_order") or execution_order,
                        request_json=usage.get("request_json"),
                        output_json=usage.get("output_json"),
                        response_json=usage.get("response_json"),
                        input_tokens=usage.get("input_tokens", 0),
                        output_tokens=usage.get("output_tokens", 0),
                        total_tokens=usage.get("total_tokens", 0),
                        estimated_cost=estimated_cost,
                        currency="USD",
                        elapsed_ms=elapsed_ms,
                        call_status=usage.get("call_status", "success"),
                        error_message=usage.get("error_message"),
                        cost_amount=estimated_cost,
                        call_time=elapsed_ms or 0,
                        started_at=_as_naive_datetime(usage.get("started_at")),
                        ended_at=_as_naive_datetime(usage.get("ended_at")),
                    )
                )
            await db.commit()
        except Exception:
            await db.rollback()
            logger.exception(
                "Failed to save LLM call logs session_id=%s candidate_id=%s",
                payload.session.session_id,
                payload.candidate.candidate_id,
            )


def _failed_response(
    payload: CandidateInterviewPrepInput,
    error: Exception,
) -> QuestionGenerationResponse:
    logger.exception("Interview question graph failed: %s", error)
    return QuestionGenerationResponse(
        session_id=payload.session.session_id,
        candidate_id=payload.candidate.candidate_id,
        target_job=payload.session.target_job,
        difficulty_level=payload.session.difficulty_level,
        status="failed",
        analysis_summary=DocumentAnalysisOutput(
            job_fit="질문 생성 파이프라인 실행 중 오류가 발생했습니다.",
            risks=[str(error)],
        ),
        questions=[],
        generation_metadata={
            "total_candidate_questions": 0,
            "selected_question_count": 0,
            "retry_count": 0,
            "router_decision": "failed",
            "is_all_approved": False,
            "error": str(error),
        },
    )


def _build_graph() -> Any:
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:
        raise RuntimeError(
            "langgraph is not installed. Install backend dependencies before running "
            "the interview question graph."
        ) from exc

    graph = StateGraph(AgentState)

    graph.add_node("build_state", build_state_node)
    graph.add_node("analyzer", analyzer_node)
    graph.add_node("questioner", questioner_node)
    graph.add_node("predictor", predictor_node)
    graph.add_node("driller", driller_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("scorer", scorer_node)
    graph.add_node("retry_questioner", increment_retry_for_questioner_node)
    graph.add_node("retry_driller", increment_retry_for_driller_node)
    graph.add_node("selector_lite", selector_lite_node)
    graph.add_node("selector", selector_node)
    graph.add_node("final_formatter", final_formatter_node)

    graph.add_edge(START, "build_state")
    graph.add_edge("build_state", "analyzer")
    graph.add_edge("analyzer", "questioner")
    graph.add_edge("questioner", "selector_lite")
    graph.add_edge("selector_lite", "predictor")
    graph.add_edge("predictor", "driller")
    graph.add_edge("driller", "reviewer")
    graph.add_edge("reviewer", "scorer")
    graph.add_conditional_edges(
        "scorer",
        route_after_scoring,
        {
            "retry_questioner": "retry_questioner",
            "retry_driller": "retry_driller",
            "selector": "selector",
        },
    )
    graph.add_edge("retry_questioner", "questioner")
    graph.add_edge("retry_driller", "driller")
    graph.add_edge("selector", "final_formatter")
    graph.add_edge("final_formatter", END)

    return graph.compile()


async def run_interview_question_graph(
    payload: CandidateInterviewPrepInput,
    on_node_complete: Callable[[str], Awaitable[None]] | None = None,
) -> QuestionGenerationResponse:
    collected_llm_usages: list[dict[str, Any]] = []
    saved_usage_count = 0
    try:
        app = _build_graph()
        initial_state: AgentState = {
            "session_id": payload.session.session_id,
            "candidate_id": payload.candidate.candidate_id,
            "candidate_name": payload.candidate.name,
            "target_job": payload.session.target_job,
            "difficulty_level": payload.session.difficulty_level,
            "prompt_profile": (
                payload.prompt_profile.model_dump(mode="json")
                if payload.prompt_profile is not None
                else None
            ),
            "documents": [
                {
                    "document_id": document.document_id,
                    "document_type": document.document_type,
                    "title": document.title,
                    "extracted_text": document.extracted_text or "",
                }
                for document in payload.candidate_documents
            ],
            "additional_instruction": getattr(payload, "additional_instruction", None),
            "human_action": getattr(payload, "human_action", None),
            "target_question_ids": getattr(payload, "target_question_ids", []),
            "dirty_question_ids": [],
            "retry_scope": None,
            "questions": getattr(payload, "existing_questions", []),
            "retry_count": 0,
            "max_retry_count": 3,
            "questioner_retry_count": 0,
            "driller_retry_count": 0,
            "max_questioner_retry_count": 1,
            "max_driller_retry_count": 1,
            "node_warnings": [],
            "llm_usages": [],
        }
        final_response: dict[str, Any] | None = None

        async for update in app.astream(initial_state, stream_mode="updates"):
            for node_name, node_update in update.items():
                if on_node_complete is not None:
                    await on_node_complete(node_name)
                llm_usages, saved_usage_count, has_llm_usages = (
                    collect_llm_usage_update(
                        node_update,
                        saved_usage_count,
                    )
                )
                if has_llm_usages:
                    collected_llm_usages.extend(llm_usages)
                else:
                    collected_llm_usages.append(
                        build_node_execution_log(
                            node_name=node_name,
                            node_update=node_update,
                        )
                    )
                if node_name == "final_formatter":
                    final_response = node_update.get("final_response")

        await save_llm_call_logs(payload=payload, usages=collected_llm_usages)

        if final_response is None:
            raise RuntimeError("Interview question graph finished without final_response.")

        return QuestionGenerationResponse.model_validate(final_response)
    except Exception as exc:  # noqa: BLE001 - service should receive typed failed result.
        await save_llm_call_logs(payload=payload, usages=collected_llm_usages)
        return _failed_response(payload, exc)
