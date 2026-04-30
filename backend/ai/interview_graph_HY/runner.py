from __future__ import annotations

"""Question generation LangGraph implementation (HY).

Per request: only this package (`backend/ai/interview_graph_HY`) is modified.
"""

from collections.abc import Awaitable, Callable

from ai.interview_graph.schemas import QuestionGenerationResponse
from schemas.session_generation import CandidateInterviewPrepInput

from .graph import build_graph


async def run_interview_question_graph(
    payload: CandidateInterviewPrepInput,
    on_node_complete: Callable[[str], Awaitable[None]] | None = None,
) -> QuestionGenerationResponse:
    app = build_graph()

    initial_state = {"_payload": payload}
    final_response: dict | None = None

    async for update in app.astream(initial_state, stream_mode="updates"):
        for node_name, node_update in update.items():
            if on_node_complete is not None:
                await on_node_complete(node_name)
            if node_name == "final":
                final_response = node_update.get("final_response")

    if final_response is None:
        raise RuntimeError("HY interview graph finished without final_response.")

    return QuestionGenerationResponse.model_validate(final_response)

