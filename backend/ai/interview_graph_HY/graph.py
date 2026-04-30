from __future__ import annotations

from typing import Any

from .nodes import (
    build_state_node,
    driller_node,
    final_formatter_node,
    increment_retry_node,
    predictor_node,
    questioner_node,
    reviewer_node,
    route_after_review,
)
from .state import AgentState


def build_graph() -> Any:
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "langgraph is not installed. Install backend dependencies before running "
            "the interview question graph."
        ) from exc

    graph = StateGraph(AgentState)

    graph.add_node("build_state", build_state_node)
    graph.add_node("questioner", questioner_node)
    graph.add_node("predictor", predictor_node)
    graph.add_node("driller", driller_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("retry", increment_retry_node)
    graph.add_node("final", final_formatter_node)

    graph.add_edge(START, "build_state")
    graph.add_edge("build_state", "questioner")
    graph.add_edge("questioner", "predictor")
    graph.add_edge("predictor", "driller")
    graph.add_edge("driller", "reviewer")
    graph.add_conditional_edges(
        "reviewer",
        route_after_review,
        {"retry": "retry", "final": "final"},
    )
    graph.add_edge("retry", "questioner")
    graph.add_edge("final", END)

    return graph.compile()
