"""면접 질문 생성 LangGraph 실행 진입점 (`interview_graph_JH`).

이 파일은 백엔드 서비스가 호출하는 공개 함수
`run_interview_question_graph()`를 제공합니다. 서비스 입력
`CandidateInterviewPrepInput`을 이 패키지의 `AgentState`로 변환하고,
LangGraph를 실행한 뒤 기존 DB 저장 로직이 사용할 수 있는
`QuestionGenerationResponse`로 변환합니다.

팀 공용 그래프의 Analyzer/Scorer/Selector 노드는 가져오지 않고,
프롬프트의 세부 제약과 최종 응답 스키마만 제품 코드에 맞춰 반영했습니다.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from ai.interview_graph.runner import save_llm_call_logs
from ai.interview_graph.schemas import DocumentAnalysisOutput, QuestionGenerationResponse
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
    """`interview_graph_JH` LangGraph 컴파일.

    [로직 순서]
    1. LangGraph 의존성 확인
    2. 설계서 기준 5개 노드만 등록
       - prepare_context → questioner → predictor → driller → reviewer
    3. Reviewer 결과가 반려면 Questioner로 재진입
    4. 승인 또는 재시도 한도 도달 시 종료

    팀 공용 그래프의 Analyzer / Scorer / Selector는 의도적으로 포함하지 않습니다.
    이후 개선 실험에서 노드 추가 여부를 비교하기 위한 기준선입니다.
    """
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:
        raise RuntimeError(
            "interview_graph_JH를 실행하려면 backend 의존성에 langgraph가 설치되어 있어야 합니다."
        ) from exc

    graph = StateGraph(AgentState)

    # [1] 설계서의 멀티 에이전트 흐름에 필요한 노드만 등록
    graph.add_node("prepare_context", prepare_context_node)
    graph.add_node("questioner", questioner_node)
    graph.add_node("predictor", predictor_node)
    graph.add_node("driller", driller_node)
    graph.add_node("reviewer", reviewer_node)

    # [2] 순차 실행: 질문 생성 → 예상 답변 → 꼬리 질문 → 품질 검수
    graph.add_edge(START, "prepare_context")
    graph.add_edge("prepare_context", "questioner")
    graph.add_edge("questioner", "predictor")
    graph.add_edge("predictor", "driller")
    graph.add_edge("driller", "reviewer")

    # [3] Reviewer가 반려하면 Questioner가 피드백을 반영해 재작성
    graph.add_conditional_edges(
        "reviewer",
        review_router,
        {
            "retry": "questioner",
            "end": END,
        },
    )
    return graph.compile()


def _normalize_existing_question(
    raw: dict[str, Any],
    index: int,
    target_question_ids: set[str],
) -> QuestionSet:
    """서비스 레이어에서 넘어온 기존 질문을 그래프 상태로 복원.

    [로직 순서]
    1. DB/서비스에서 직렬화된 질문 dict를 읽음
    2. 그래프가 사용하는 QuestionSet 필드명으로 정규화
    3. 기존 질문은 기본 approved 상태로 유지
    4. 서비스 레이어가 지정한 재생성 대상은 human_rejected 상태로 복원
    """
    question_id = str(raw.get("id") or f"existing-{index + 1}")
    is_regeneration_target = question_id in target_question_ids
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
        "follow_up_question": str(raw.get("follow_up_question") or ""),
        "follow_up_basis": str(raw.get("follow_up_basis") or ""),
        "risk_tags": list(raw.get("risk_tags") or []),
        "competency_tags": list(raw.get("competency_tags") or []),
        "review_status": str(raw.get("review_status") or "needs_revision"),
        "review_reason": str(raw.get("review_reason") or ""),
        "reject_reason": str(raw.get("reject_reason") or raw.get("review_reject_reason") or ""),
        "recommended_revision": str(raw.get("recommended_revision") or ""),
        "score": int(raw.get("score") or 75),
        "score_reason": str(raw.get("score_reason") or ""),
        "status": "human_rejected" if is_regeneration_target else "approved",
        "regen_targets": list(raw.get("regen_targets") or []),
    }


def _initial_state(payload: CandidateInterviewPrepInput) -> AgentState:
    """백엔드 서비스 입력을 그래프의 초기 State로 변환.

    [로직 순서]
    1. 세션/지원자/직무/난이도 정보를 상태에 주입
    2. 프롬프트 프로필과 지원자 문서 목록을 그래프 입력 형태로 변환
    3. 재생성 호출이면 기존 질문을 QuestionSet으로 복원
    4. retry, human_action, usage 로그 등 제어 필드를 초기화
    """
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
        "llm_usages": [],
        "node_warnings": [],
    }


def _failed_response(
    payload: CandidateInterviewPrepInput,
    error: Exception,
) -> QuestionGenerationResponse:
    logger.exception("interview_graph_JH 실행 실패: %s", error)
    return QuestionGenerationResponse(
        session_id=payload.session.session_id,
        candidate_id=payload.candidate.candidate_id,
        target_job=payload.session.target_job,
        difficulty_level=payload.session.difficulty_level,
        status="failed",
        analysis_summary=DocumentAnalysisOutput(
            job_fit="면접 질문 생성 그래프 실행 중 오류가 발생했습니다.",
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
    """면접 질문 생성 그래프 실행 (`interview_graph_JH`).

    [로직 순서]
    1. LangGraph 컴파일
    2. 서비스 입력(payload)을 AgentState로 변환
    3. LangGraph를 스트리밍 실행하며 노드 완료 콜백/LLM 사용량 수집
    4. 최종 State를 기존 서비스가 저장 가능한 QuestionGenerationResponse로 변환
    5. LLM 사용량을 기존 로그 테이블에 저장
    6. 실패 시 failed 응답으로 변환해 백그라운드 잡이 세션 상태를 실패 처리하도록 함
    """
    collected_llm_usages: list[dict[str, Any]] = []
    try:
        # [1] 그래프 준비 + 입력 상태 초기화
        app = _build_graph()
        final_state = _initial_state(payload)

        # [2] 노드별 실행 결과를 누적해 최종 상태를 구성
        # 각 노드는 partial dict를 반환하고, llm_usages는 항상 누적된 전체 리스트를
        # 포함해 반환하므로 latest 값으로 덮어쓰면 그것이 최신 누적치가 된다.
        async for update in app.astream(final_state, stream_mode="updates"):
            for node_name, node_update in update.items():
                if on_node_complete is not None:
                    await on_node_complete(node_name)
                if isinstance(node_update, dict):
                    final_state.update(node_update)
                    if "llm_usages" in node_update:
                        collected_llm_usages = list(node_update["llm_usages"])

        # [3] 제품 저장 스키마로 변환 후 비용/토큰 로그 저장
        response = build_response(final_state)
        await save_llm_call_logs(payload=payload, usages=collected_llm_usages)
        return response
    except Exception as exc:  # noqa: BLE001 - service should receive typed failed result.
        await save_llm_call_logs(payload=payload, usages=collected_llm_usages)
        return _failed_response(payload, exc)
