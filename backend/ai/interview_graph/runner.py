import logging
from collections.abc import Awaitable, Callable
from typing import Any

from ai.interview_graph.nodes import (
    analyzer_node,
    build_state_node,
    driller_node,
    final_formatter_node,
    predictor_node,
    questioner_node,
    reviewer_node,
    scorer_node,
    selector_lite_node,
    selector_node,
)
from ai.interview_graph.schemas import DocumentAnalysisOutput, QuestionGenerationResponse
from ai.interview_graph.state import AgentState
from schemas.session_generation import CandidateInterviewPrepInput

logger = logging.getLogger(__name__)


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
    graph.add_node("selector_lite", selector_lite_node)
    graph.add_node("selector", selector_node)
    graph.add_node("final_formatter", final_formatter_node)

    graph.add_edge(START, "build_state")
    graph.add_edge("build_state", "analyzer")
    graph.add_edge("analyzer", "questioner")
    graph.add_edge("questioner", "selector_lite")
    graph.add_edge("selector_lite", "predictor")
    graph.add_edge("selector_lite", "driller")
    graph.add_edge("selector_lite", "reviewer")
    graph.add_edge(["predictor", "driller", "reviewer"], "scorer")
    graph.add_edge("scorer", "selector")
    graph.add_edge("selector", "final_formatter")
    graph.add_edge("final_formatter", END)

    return graph.compile()


async def run_interview_question_graph(
    payload: CandidateInterviewPrepInput,
    on_node_complete: Callable[[str], Awaitable[None]] | None = None,
) -> QuestionGenerationResponse:
    try:
        app = _build_graph()
        initial_state: AgentState = {
            "source_payload": payload.model_dump(mode="json"),
            "retry_count": 0,
            "max_retry_count": 3,
            "node_warnings": [],
        }
        final_response: dict[str, Any] | None = None

        async for update in app.astream(initial_state, stream_mode="updates"):
            for node_name, node_update in update.items():
                if on_node_complete is not None:
                    await on_node_complete(node_name)
                if node_name == "final_formatter":
                    final_response = node_update.get("final_response")

        if final_response is None:
            raise RuntimeError("Interview question graph finished without final_response.")

        return QuestionGenerationResponse.model_validate(final_response)
    except Exception as exc:  # noqa: BLE001 - service should receive typed failed result.
        return _failed_response(payload, exc)
