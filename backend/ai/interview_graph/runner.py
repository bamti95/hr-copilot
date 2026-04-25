import logging
from typing import Any

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
    selector_node,
)
from ai.interview_graph.router import route_after_scoring
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
    graph.add_node("retry_questioner", increment_retry_for_questioner_node)
    graph.add_node("retry_driller", increment_retry_for_driller_node)
    graph.add_node("selector", selector_node)
    graph.add_node("final_formatter", final_formatter_node)

    graph.add_edge(START, "build_state")
    graph.add_edge("build_state", "analyzer")
    graph.add_edge("analyzer", "questioner")
    graph.add_edge("questioner", "predictor")
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
) -> QuestionGenerationResponse:
    try:
        app = _build_graph()
        initial_state: AgentState = {
            "source_payload": payload.model_dump(mode="json"),
            "retry_count": 0,
            "max_retry_count": 3,
        }
        result = await app.ainvoke(initial_state)
        return QuestionGenerationResponse.model_validate(result["final_response"])
    except Exception as exc:  # noqa: BLE001 - service should receive typed failed result.
        return _failed_response(payload, exc)
