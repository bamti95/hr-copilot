"""JH 그래프 실행 진입점.

이 파일은 서비스 레이어가 JH 그래프를 호출할 때 사용하는 공개 함수와
초기 state 구성 로직을 담고 있다.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from ai.graph_usage import collect_llm_usage_update
from ai.interview_graph.runner import build_node_execution_log, save_llm_call_logs
from ai.interview_graph_JH.schemas import DocumentAnalysisOutput, QuestionGenerationResponse
from ai.interview_graph_JH.nodes import (
    build_response,
    driller_node,
    prepare_context_node,
    predictor_node,
    questioner_node,
    review_router,
    reviewer_node,
)
from ai.interview_graph_JH.state import AgentState, QuestionSet
from schemas.session_generation import CandidateInterviewPrepInput

logger = logging.getLogger(__name__)


def _build_graph() -> Any:
    """LangGraph 객체를 구성한다."""
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:
        raise RuntimeError(
            "interview_graph_JH를 실행하려면 backend 환경에 langgraph가 설치되어 있어야 합니다."
        ) from exc

    graph = StateGraph(AgentState)
    graph.add_node("prepare_context", prepare_context_node)
    graph.add_node("questioner", questioner_node)
    graph.add_node("predictor", predictor_node)
    graph.add_node("driller", driller_node)
    graph.add_node("reviewer", reviewer_node)

    graph.add_edge(START, "prepare_context")
    graph.add_edge("prepare_context", "questioner")
    graph.add_edge("questioner", "predictor")
    graph.add_edge("predictor", "driller")
    graph.add_edge("driller", "reviewer")
    graph.add_conditional_edges(
        "reviewer",
        review_router,
        {"retry": "questioner", "end": END},
    )
    return graph.compile()


def _normalize_existing_question(
    raw: dict[str, Any],
    index: int,
    target_question_ids: set[str],
) -> QuestionSet:
    """DB/서비스에서 넘어온 기존 질문을 그래프 내부 QuestionSet으로 맞춘다."""
    question_id = str(raw.get("id") or f"existing-{index + 1}")
    is_regeneration_target = question_id in target_question_ids
    requested_fields = [str(item) for item in raw.get("requested_revision_fields") or []]
    return {
        "id": question_id,
        "category": str(raw.get("category") or "OTHER"),
        "question_text": str(raw.get("question_text") or ""),
        "generation_basis": str(
            raw.get("generation_basis") or raw.get("question_rationale") or ""
        ),
        "document_evidence": list(raw.get("document_evidence") or []),
        "evaluation_guide": str(raw.get("evaluation_guide") or ""),
        "predicted_answer": str(raw.get("predicted_answer") or raw.get("expected_answer") or ""),
        "predicted_answer_basis": str(raw.get("predicted_answer_basis") or ""),
        "answer_confidence": str(raw.get("answer_confidence") or ""),
        "answer_risk_points": list(raw.get("answer_risk_points") or []),
        "follow_up_question": str(raw.get("follow_up_question") or ""),
        "follow_up_basis": str(raw.get("follow_up_basis") or ""),
        "drill_type": str(raw.get("drill_type") or ""),
        "risk_tags": list(raw.get("risk_tags") or []),
        "competency_tags": list(raw.get("competency_tags") or []),
        "review_status": str(raw.get("review_status") or "needs_revision"),
        "review_reason": str(raw.get("review_reason") or ""),
        "reject_reason": str(raw.get("reject_reason") or raw.get("review_reject_reason") or ""),
        "recommended_revision": str(raw.get("recommended_revision") or ""),
        "review_issue_types": list(raw.get("review_issue_types") or []),
        "requested_revision_fields": requested_fields,
        "question_quality_scores": dict(raw.get("question_quality_scores") or {}),
        "evaluation_guide_scores": dict(raw.get("evaluation_guide_scores") or {}),
        "question_quality_average": float(raw.get("question_quality_average") or 0.0),
        "evaluation_guide_average": float(raw.get("evaluation_guide_average") or 0.0),
        "score": float(raw.get("score") or 0.0),
        "score_reason": str(raw.get("score_reason") or ""),
        "status": "human_rejected" if is_regeneration_target else "approved",
        "regen_targets": list(raw.get("regen_targets") or requested_fields),
        "generation_mode": str(raw.get("generation_mode") or "initial"),
    }


def _initial_generation_mode(payload: CandidateInterviewPrepInput) -> str:
    """human_action을 그래프 내부 generation_mode로 변환한다."""
    action = str(payload.human_action or "").strip()
    if action in {"more", "more_questions"}:
        return "more"
    if action in {"add_question", "generate_follow_up", "risk_questions", "different_perspective"}:
        return "add_question"
    if action in {"regenerate", "regenerate_question"}:
        return "partial_rewrite"
    return "initial"


def _initial_state(payload: CandidateInterviewPrepInput) -> AgentState:
    """그래프 실행 전에 사용할 초기 state를 만든다."""
    target_question_ids = {str(question_id) for question_id in payload.target_question_ids}
    return {
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
        "candidate_context": "",
        "questions": [
            _normalize_existing_question(question, index, target_question_ids)
            for index, question in enumerate(payload.existing_questions)
        ],
        "retry_count": 0,
        "max_retry_count": 3,
        "is_all_approved": False,
        "human_action": payload.human_action,
        "additional_instruction": payload.additional_instruction,
        "target_question_ids": payload.target_question_ids,
        "generation_mode": _initial_generation_mode(payload),
        "llm_usages": [],
        "node_warnings": [],
    }


def _failed_response(
    payload: CandidateInterviewPrepInput,
    error: Exception,
) -> QuestionGenerationResponse:
    """그래프 실행 실패 시 서비스가 받을 fallback 응답."""
    logger.exception("interview_graph_JH 실행 실패: %s", error)
    return QuestionGenerationResponse(
        session_id=payload.session.session_id,
        candidate_id=payload.candidate.candidate_id,
        target_job=payload.session.target_job,
        difficulty_level=payload.session.difficulty_level,
        status="failed",
        analysis_summary=DocumentAnalysisOutput(
            job_fit="JH 면접 질문 그래프 실행 중 오류가 발생했습니다.",
            risks=[str(error)],
        ),
        questions=[],
        generation_metadata={
            "pipeline": "jh",
            "total_candidate_questions": 0,
            "selected_question_count": 0,
            "retry_count": 0,
            "is_all_approved": False,
            "error": str(error),
        },
    )


async def run_interview_question_graph(
    payload: CandidateInterviewPrepInput,
    on_node_complete: Callable[[str], Awaitable[None]] | None = None,
) -> QuestionGenerationResponse:
    """JH 그래프를 실행하고 최종 응답 객체를 반환한다."""
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
                    llm_usages, saved_usage_count, has_llm_usages = (
                        collect_llm_usage_update(
                            node_update,
                            saved_usage_count,
                            cumulative=True,
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

        response = build_response(final_state)
        await save_llm_call_logs(payload=payload, usages=collected_llm_usages)
        return response
    except Exception as exc:  # noqa: BLE001
        await save_llm_call_logs(payload=payload, usages=collected_llm_usages)
        return _failed_response(payload, exc)
