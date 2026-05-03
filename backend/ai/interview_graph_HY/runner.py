"""질문 생성 LangGraph 진입점 (`interview_graph_HY`).

이 모듈과 `interview_graph_HY` 패키지만 수정하면 다른 파이프라인 구현에는 영향이 없습니다.
현재는 동작 연결을 위해 공용 그래프에 위임합니다.
"""

from collections.abc import Awaitable, Callable

from ai.graph_usage import collect_llm_usage_update as _collect_llm_usage_update
from ai.interview_graph.schemas import QuestionGenerationResponse
from schemas.session_generation import CandidateInterviewPrepInput

_ = _collect_llm_usage_update


async def run_interview_question_graph(
    payload: CandidateInterviewPrepInput,
    on_node_complete: Callable[[str], Awaitable[None]] | None = None,
) -> QuestionGenerationResponse:
    from ai.interview_graph.runner import run_interview_question_graph as run_default

    return await run_default(payload, on_node_complete=on_node_complete)
