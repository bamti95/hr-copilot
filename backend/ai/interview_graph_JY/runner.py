"""JY LangGraph runner.

`interview_graph_JY` 전용 멀티에이전트 질문 생성 파이프라인이다.
서비스 레이어의 공개 인터페이스는 공용 그래프와 동일하게 유지한다.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from ai.graph_usage import collect_llm_usage_update
from ai.interview_graph.runner import build_node_execution_log, save_llm_call_logs
from ai.interview_graph_JY.schemas import DocumentAnalysisOutput, QuestionGenerationResponse
from ai.interview_graph_JY.nodes import (
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
from ai.interview_graph_JY.router import route_after_review
from ai.interview_graph_JY.state import AgentState
from schemas.session_generation import CandidateInterviewPrepInput

logger = logging.getLogger(__name__)


def _build_graph() -> Any:
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:
        raise RuntimeError(
            "interview_graph_JY를 실행하려면 backend 환경에 langgraph가 설치되어 있어야 합니다."
        ) from exc

    graph = StateGraph(AgentState)
    graph.add_node("build_state", build_state_node)
    graph.add_node("analyzer", analyzer_node)
    graph.add_node("questioner", questioner_node)
    graph.add_node("predictor", predictor_node)
    graph.add_node("driller", driller_node)
    graph.add_node("driller_retry_run", driller_node)
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
    graph.add_edge("selector_lite", "driller")
    graph.add_edge(["predictor", "driller"], "reviewer")
    graph.add_edge("reviewer", "scorer")
    graph.add_conditional_edges(
        "scorer",
        route_after_review,
        {
            "retry_questioner": "retry_questioner",
            "retry_driller": "retry_driller",
            "selector": "selector",
        },
    )
    graph.add_edge("retry_questioner", "questioner")
    graph.add_edge("retry_driller", "driller_retry_run")
    graph.add_edge("driller_retry_run", "reviewer")
    graph.add_edge("selector", "final_formatter")
    graph.add_edge("final_formatter", END)
    return graph.compile()


def _initial_state(payload: CandidateInterviewPrepInput) -> AgentState:
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
        "additional_instruction": getattr(payload, "additional_instruction", None),
        "human_action": getattr(payload, "human_action", None),
        "target_question_ids": list(getattr(payload, "target_question_ids", []) or []),
        "questions": list(getattr(payload, "existing_questions", []) or []),
        "retry_count": 0,
        "max_retry_count": 2,
        "questioner_retry_count": 0,
        "driller_retry_count": 0,
        "max_questioner_retry_count": 1,
        "max_driller_retry_count": 1,
        "llm_usages": [],
        "node_warnings": [],
    }


def _failed_response(
    payload: CandidateInterviewPrepInput,
    error: Exception,
) -> QuestionGenerationResponse:
    logger.exception("interview_graph_JY 실행 실패: %s", error)
    return QuestionGenerationResponse(
        session_id=payload.session.session_id,
        candidate_id=payload.candidate.candidate_id,
        target_job=payload.session.target_job,
        difficulty_level=payload.session.difficulty_level,
        status="failed",
        analysis_summary=DocumentAnalysisOutput(
            job_fit="JY 면접 질문 그래프 실행 중 오류가 발생했습니다.",
            risks=[str(error)],
        ),
        questions=[],
        generation_metadata={
            "pipeline": "jy",
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
    collected_llm_usages: list[dict[str, Any]] = []
    saved_usage_count = 0
    llm_logs_saved = False

    async def persist_llm_logs_once() -> None:
        nonlocal llm_logs_saved
        if llm_logs_saved:
            return
        await save_llm_call_logs(payload=payload, usages=collected_llm_usages)
        llm_logs_saved = True

    try:
        app = _build_graph()
        initial_state = _initial_state(payload)
        final_response: dict[str, Any] | None = None

        async for update in app.astream(initial_state, stream_mode="updates"):
            for node_name, node_update in update.items():
                if on_node_complete is not None:
                    await on_node_complete(node_name)
                llm_usages, saved_usage_count, has_llm_usages = collect_llm_usage_update(
                    node_update,
                    saved_usage_count,
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

        await persist_llm_logs_once()
        if final_response is None:
            raise RuntimeError("JY graph finished without final_response.")
        return QuestionGenerationResponse.model_validate(final_response)
    except Exception as exc:  # noqa: BLE001
        await persist_llm_logs_once()
        return _failed_response(payload, exc)
