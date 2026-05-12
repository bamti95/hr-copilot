"""Entry point for the JH interview-question LangGraph."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from ai.graph_usage import collect_llm_usage_update
from ai.interview_graph_JH.nodes import (
    build_response,
    driller_node,
    predictor_node,
    prepare_context_node,
    questioner_node,
    review_router,
    reviewer_node,
    verification_point_extractor_node,
)
from ai.interview_graph_JH.schemas import (
    DocumentAnalysisOutput,
    QuestionGenerationResponse,
)
from ai.interview_graph_JH.state import AgentState, QuestionSet
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


def build_node_execution_log(*, node_name: str, node_update: Any) -> dict[str, Any]:
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
                "Failed to save JH LLM call logs session_id=%s candidate_id=%s",
                payload.session.session_id,
                payload.candidate.candidate_id,
            )


def _build_graph() -> Any:
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:
        raise RuntimeError(
            "langgraph is not installed. Install backend dependencies before running "
            "interview_graph_JH."
        ) from exc

    graph = StateGraph(AgentState)
    graph.add_node("prepare_context", prepare_context_node)
    graph.add_node("verification_point_extractor", verification_point_extractor_node)
    graph.add_node("questioner", questioner_node)
    graph.add_node("predictor", predictor_node)
    graph.add_node("driller", driller_node)
    graph.add_node("reviewer", reviewer_node)

    graph.add_edge(START, "prepare_context")
    graph.add_edge("prepare_context", "verification_point_extractor")
    graph.add_edge("verification_point_extractor", "questioner")
    graph.add_edge("questioner", "predictor")
    graph.add_edge("predictor", "driller")
    graph.add_edge("driller", "reviewer")
    graph.add_conditional_edges(
        "reviewer",
        review_router,
        {"retry": "questioner", "end": END},
    )
    return graph.compile()


def _normalize_document_evidence(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = [text]
        else:
            if not isinstance(parsed, list):
                parsed = [parsed]
    elif isinstance(value, list):
        parsed = value
    else:
        parsed = [value]
    return [str(item).strip() for item in parsed if str(item).strip()]


def _score_to_five(value: Any) -> float:
    try:
        score = float(value or 0)
    except (TypeError, ValueError):
        return 0.0
    if score > 5:
        return round(score / 20, 2)
    return score


def _normalize_action(action: Any) -> str:
    action_text = str(action or "").strip()
    if action_text in {"regenerate", "regenerate_question"}:
        return "regenerate_selected"
    if action_text in {"more", "more_questions", "add_question"}:
        return "add_question"
    return "generate"


def _clip_text(value: Any, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3].rstrip()}..."


def _prompt_profile_summary_text(payload: CandidateInterviewPrepInput) -> str:
    profile = payload.prompt_profile
    if profile is None:
        return ""

    parts = [
        f"프로필 키: {profile.profile_key}",
        f"프로필 대상 직무: {profile.target_job or payload.session.target_job or ''}",
    ]
    if profile.system_prompt:
        parts.append(f"프로필 시스템 프롬프트 요약: {_clip_text(profile.system_prompt, 3000)}")
    if profile.output_schema:
        parts.append(
            "프로필 출력 스키마: "
            + _clip_text(json.dumps(profile.output_schema, ensure_ascii=False), 1500)
        )
    return "\n".join(part for part in parts if part)


def _build_job_posting_context(payload: CandidateInterviewPrepInput) -> str:
    parts = [f"채용 직무명: {payload.session.target_job}"]
    profile_summary = _prompt_profile_summary_text(payload)
    if profile_summary:
        parts.append(profile_summary)
    return "\n\n".join(part for part in parts if part).strip()


def _normalize_existing_question(
    raw: dict[str, Any],
    index: int,
    target_question_ids: set[str],
) -> QuestionSet:
    question_id = str(raw.get("id") or f"existing-{index + 1}")
    is_target = question_id in target_question_ids
    status = "human_rejected" if is_target else "approved"
    score = _score_to_five(raw.get("score")) or 4.0
    review_reason = str(raw.get("review_reason") or "")
    score_reason = str(raw.get("score_reason") or raw.get("review_reason") or "")
    recommended_revision = str(raw.get("recommended_revision") or "")
    rewrite_feedback_parts = [
        f"이전 상태: {raw.get('review_status') or 'unknown'}",
        f"리뷰 사유: {review_reason}" if review_reason else "",
        f"점수 사유: {score_reason}" if score_reason else "",
        f"권장 수정: {recommended_revision}" if recommended_revision else "",
    ]
    return {
        "id": question_id,
        "original_question_id": question_id,
        "category": str(raw.get("category") or "직무역량"),
        "question_text": str(raw.get("question_text") or ""),
        "generation_basis": str(
            raw.get("generation_basis") or raw.get("question_rationale") or ""
        ),
        "document_evidence": _normalize_document_evidence(raw.get("document_evidence")),
        "evaluation_guide": str(raw.get("evaluation_guide") or ""),
        "predicted_answer": str(raw.get("predicted_answer") or raw.get("expected_answer") or ""),
        "predicted_answer_basis": str(raw.get("predicted_answer_basis") or ""),
        "follow_up_questions": _normalize_document_evidence(raw.get("follow_up_questions"))
        or _normalize_document_evidence(raw.get("follow_up_question")),
        "follow_up_intents": _normalize_document_evidence(raw.get("follow_up_intents"))
        or _normalize_document_evidence(raw.get("follow_up_basis")),
        "review_status": "pending" if is_target else "approved",
        "review_reason": review_reason,
        "reject_reason": str(raw.get("reject_reason") or raw.get("review_reject_reason") or ""),
        "recommended_revision": recommended_revision,
        "review_issue_types": list(raw.get("review_issue_types") or []),
        "requested_revision_fields": list(raw.get("requested_revision_fields") or []),
        "question_quality_scores": dict(raw.get("question_quality_scores") or {}),
        "evaluation_guide_scores": dict(raw.get("evaluation_guide_scores") or {}),
        "question_quality_average": float(raw.get("question_quality_average") or 4.0),
        "evaluation_guide_average": float(raw.get("evaluation_guide_average") or 4.0),
        "score": 0.0 if is_target else score,
        "score_reason": score_reason,
        "status": status,
        "is_selectable": not is_target,
        "selection_reason": score_reason or review_reason,
        "review_strengths": [],
        "review_risks": list(raw.get("risk_tags") or []),
        "previous_review_status": str(raw.get("review_status") or ""),
        "previous_review_reason": review_reason,
        "previous_score_reason": score_reason,
        "previous_recommended_revision": recommended_revision,
        "previous_score": score,
        "rewrite_feedback": "\n".join(
            part for part in rewrite_feedback_parts if part
        ),
    }


def _document_bucket(payload: CandidateInterviewPrepInput) -> dict[str, str]:
    bucket = {"resume": [], "cover_letter": [], "portfolio": []}
    for document in payload.candidate_documents:
        doc_type = str(document.document_type or "").lower()
        text = document.extracted_text or ""
        if not text:
            continue
        if "cover" in doc_type or "자소" in doc_type or "소개" in doc_type:
            bucket["cover_letter"].append(text)
        elif "portfolio" in doc_type or "포트" in doc_type:
            bucket["portfolio"].append(text)
        else:
            bucket["resume"].append(text)
    return {key: "\n\n".join(values) for key, values in bucket.items()}


def _initial_state(payload: CandidateInterviewPrepInput) -> AgentState:
    target_question_ids = {str(question_id) for question_id in payload.target_question_ids}
    documents = _document_bucket(payload)
    action = _normalize_action(payload.human_action)
    prompt_profile_summary = _prompt_profile_summary_text(payload)
    return {
        "session_id": payload.session.session_id,
        "candidate_id": payload.candidate.candidate_id,
        "target_job": payload.session.target_job,
        "difficulty_level": payload.session.difficulty_level,
        "job_posting": _build_job_posting_context(payload),
        "prompt_profile_key": payload.prompt_profile.profile_key if payload.prompt_profile else None,
        "prompt_profile_target_job": (
            payload.prompt_profile.target_job if payload.prompt_profile else None
        ),
        "prompt_profile_system_prompt": (
            payload.prompt_profile.system_prompt if payload.prompt_profile else None
        ),
        "prompt_profile_output_schema": (
            payload.prompt_profile.output_schema if payload.prompt_profile else None
        ),
        "prompt_profile_summary": prompt_profile_summary,
        "company_name": getattr(payload.session, "company_name", None),
        "applicant_name": payload.candidate.name,
        "resume": documents["resume"],
        "cover_letter": documents["cover_letter"],
        "portfolio": documents["portfolio"],
        "existing_questions": payload.existing_questions,
        "questions": [
            _normalize_existing_question(question, index, target_question_ids)
            for index, question in enumerate(payload.existing_questions)
        ],
        "human_action": action,
        "selected_question_ids": list(target_question_ids),
        "feedback": payload.additional_instruction,
        "requested_count": 5,
        "retry_count": 0,
        "max_retry_count": 2,
        "is_all_approved": False,
        "errors": [],
        "raw_outputs": {},
        "llm_usages": [],
    }


def _failed_response(
    payload: CandidateInterviewPrepInput,
    error: Exception,
) -> QuestionGenerationResponse:
    logger.exception("interview_graph_JH failed: %s", error)
    return QuestionGenerationResponse(
        session_id=payload.session.session_id,
        candidate_id=payload.candidate.candidate_id,
        target_job=payload.session.target_job,
        difficulty_level=payload.session.difficulty_level,
        status="failed",
        analysis_summary=DocumentAnalysisOutput(
            job_fit="면접 질문 그래프 실행 중 오류가 발생했습니다.",
            risks=[str(error)],
        ),
        questions=[],
        generation_metadata={
            "pipeline": "interview_graph_JH",
            "candidate_count": 0,
            "selected_count": 0,
            "retry_count": 0,
            "error": str(error),
        },
    )


async def run_interview_question_graph(
    payload: CandidateInterviewPrepInput,
    on_node_complete: Callable[[str], Awaitable[None]] | None = None,
) -> QuestionGenerationResponse:
    collected_llm_usages: list[dict[str, Any]] = []
    saved_usage_count = 0
    try:
        app = _build_graph()
        final_state = _initial_state(payload)

        async for update in app.astream(final_state, stream_mode="updates"):
            for node_name, node_update in update.items():
                if on_node_complete is not None:
                    await on_node_complete(node_name)
                if isinstance(node_update, dict):
                    final_state.update(node_update)
                llm_usages, saved_usage_count, has_llm_usages = collect_llm_usage_update(
                    node_update,
                    saved_usage_count,
                    cumulative=False,
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

        response = build_response(final_state)
        await save_llm_call_logs(payload=payload, usages=collected_llm_usages)
        return response
    except Exception as exc:  # noqa: BLE001
        await save_llm_call_logs(payload=payload, usages=collected_llm_usages)
        return _failed_response(payload, exc)
