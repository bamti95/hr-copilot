import asyncio
import json
import logging
from typing import Any, TypeVar

from pydantic import BaseModel

from ai.interview_graph import prompts
from ai.interview_graph.schemas import (
    DocumentAnalysisOutput,
    DrillerOutput,
    FollowUpQuestion,
    InterviewQuestionItem,
    PredictedAnswer,
    PredictorOutput,
    QuestionCandidate,
    QuestionGenerationResponse,
    QuestionerOutput,
    ReviewResult,
    ReviewerOutput,
    ScoreResult,
    ScorerOutput,
)
from ai.interview_graph.state import AgentState
from ai.llm_client import client, get_openai_model
from core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

MAX_DOCUMENT_CHARS = 18000
PREDICTOR_DOCUMENT_CHARS = 6000

APPROVED_REVIEW_STATUSES = {"approved"}
FOLLOW_UP_WEAK_FLAGS = {
    "FOLLOW_UP_TOO_WEAK",
    "꼬리질문_약함",
    "꼬리질문_연결성_부족",
    "꼬리질문_보강_필요",
}
QUESTION_REWRITE_FLAGS = {
    "QUESTION_TOO_GENERIC",
    "EVIDENCE_TOO_WEAK",
    "LOW_JOB_RELEVANCE",
    "DUPLICATE_RISK",
    "질문_일반적",
    "문서_근거_부족",
    "직무_관련성_부족",
    "중복_위험",
    "보완_필요",
    "재작성_권장",
}
RISK_CATEGORIES = {"RISK", "리스크"}

# LLM 응답을 Pydantic 모델로 강제 파싱 + 검증 + 재시도 하는 래퍼
async def _call_structured_output(
    *,
    system_prompt: str,
    user_prompt: str,
    response_model: type[T],
) -> T:
    '''
    system_prompt, user_prompt -> LLM 입력
    response_model -> 출력 스키마 (Pydantic)
    text_format=response_model이
    LLM -> JSON -> Pydantic 객체 자동 변환
    '''
    last_error: Exception | None = None
    for _ in range(2):
        try:
            response = await asyncio.wait_for(
                client.responses.parse(
                    model=get_openai_model(),
                    input=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    text_format=response_model,
                ),
                timeout=settings.OPENAI_TIMEOUT_SECONDS,
            )
            parsed = response.output_parsed
            if parsed is None:
                raise ValueError("Structured output was empty.")
            return parsed
        except Exception as exc:  # noqa: BLE001 - preserve original SDK/validation error.
            last_error = exc
            logger.warning(
                "Structured output call failed for %s: %s",
                response_model.__name__,
                exc,
            )
    raise RuntimeError(
        f"Structured output call failed for {response_model.__name__}"
    ) from last_error


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _clip_text(value: str, max_chars: int) -> str:
    text = value.strip()
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars]}\n\n...(입력 길이 제한으로 일부 문서 텍스트를 생략했습니다.)"


def _clip_sentence(value: str, max_chars: int) -> str:
    text = " ".join(value.split())
    if len(text) <= max_chars:
        return text
    return f"{text[: max_chars - 1].rstrip()}…"


def _compact_predicted_answer(answer: dict[str, Any]) -> dict[str, Any]:
    return {
        **answer,
        "predicted_answer": _clip_sentence(
            str(answer.get("predicted_answer") or ""),
            300,
        ),
        "predicted_answer_basis": _clip_sentence(
            str(answer.get("predicted_answer_basis") or ""),
            160,
        ),
    }


def _merge_document_text(payload: dict[str, Any]) -> tuple[str, bool]:
    candidate = payload.get("candidate", {})
    session = payload.get("session", {})
    documents = payload.get("candidate_documents", [])

    sections = [
        "[Session]",
        f"target_job: {session.get('target_job')}",
        f"difficulty_level: {session.get('difficulty_level')}",
        "",
        "[Candidate]",
        f"candidate_id: {candidate.get('candidate_id')}",
        f"name: {candidate.get('name')}",
        f"job_position: {candidate.get('job_position')}",
        f"apply_status: {candidate.get('apply_status')}",
    ]

    has_extracted_text = False
    remaining_chars = MAX_DOCUMENT_CHARS

    for document in documents:
        extracted_text = (document.get("extracted_text") or "").strip()
        if extracted_text:
            has_extracted_text = True
        if remaining_chars <= 0:
            break

        clipped = extracted_text[:remaining_chars]
        remaining_chars -= len(clipped)
        sections.extend(
            [
                "",
                "[Document]",
                f"document_id: {document.get('document_id')}",
                f"document_type: {document.get('document_type')}",
                f"title: {document.get('title')}",
                f"extract_status: {document.get('extract_status')}",
                "extracted_text:",
                clipped or "(no extracted text)",
            ]
        )

    return "\n".join(sections), has_extracted_text


def _question_id(question: dict[str, Any], index: int) -> str:
    value = str(question.get("id") or "").strip()
    return value or f"q_{index + 1:03d}"


def _find_by_question_id(items: list[dict[str, Any]], question_id: str) -> dict[str, Any]:
    return next((item for item in items if item.get("question_id") == question_id), {})


def _is_approved_review(review: dict[str, Any]) -> bool:
    return review.get("status") in APPROVED_REVIEW_STATUSES


def _is_risk_question(question: dict[str, Any]) -> bool:
    return (
        question.get("category") in RISK_CATEGORIES
        or bool(question.get("risk_tags"))
    )


def _select_question_candidates(
    questions: list[dict[str, Any]],
    *,
    reviews_by_id: dict[str, dict[str, Any]] | None = None,
    scores_by_id: dict[str, dict[str, Any]] | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    reviews_by_id = reviews_by_id or {}
    scores_by_id = scores_by_id or {}

    unique_questions: list[dict[str, Any]] = []
    seen_texts: set[str] = set()
    for question in questions:
        text_key = " ".join(str(question.get("question_text", "")).split()).lower()
        if not text_key or text_key in seen_texts:
            continue
        seen_texts.add(text_key)
        unique_questions.append(question)

    sorted_questions = sorted(
        unique_questions,
        key=lambda question: (
            _is_approved_review(reviews_by_id.get(question.get("id"), {})),
            scores_by_id.get(question.get("id"), {}).get("score", 0),
            bool(question.get("document_evidence")),
            _is_risk_question(question),
        ),
        reverse=True,
    )

    selected: list[dict[str, Any]] = []
    used_categories: set[str] = set()

    risk_question = next(
        (
            question
            for question in sorted_questions
            if _is_risk_question(question)
        ),
        None,
    )
    if risk_question:
        selected.append(risk_question)
        used_categories.add(str(risk_question.get("category")))

    for question in sorted_questions:
        if len(selected) >= limit:
            break
        if question in selected:
            continue
        category = str(question.get("category"))
        if category in used_categories and len(selected) < 3:
            continue
        selected.append(question)
        used_categories.add(category)

    for question in sorted_questions:
        if len(selected) >= limit:
            break
        if question not in selected:
            selected.append(question)

    return selected


def _build_retry_feedback(state: AgentState) -> str:
    summary = state.get("review_summary", {})
    reviews = state.get("reviews", [])
    scores = state.get("scores", [])

    rejected_reviews = [
        {
            "question_id": review.get("question_id"),
            "status": review.get("status"),
            "reason": review.get("reason"),
            "reject_reason": review.get("reject_reason"),
            "recommended_revision": review.get("recommended_revision"),
        }
        for review in reviews
        if not _is_approved_review(review)
    ][:5]
    low_scores = [
        {
            "question_id": score.get("question_id"),
            "score": score.get("score"),
            "score_reason": score.get("score_reason"),
            "quality_flags": score.get("quality_flags", []),
        }
        for score in scores
        if score.get("score", 0) < 80
    ][:5]

    return _json(
        {
            "retry_reason": "Router judged that the generated result needs improvement.",
            "approved_count": summary.get("approved_count", 0),
            "avg_score": summary.get("avg_score", 0),
            "quality_issues": summary.get("quality_issues", []),
            "rejected_or_revision_reviews": rejected_reviews,
            "low_score_questions": low_scores,
            "instruction": (
                "이 피드백을 반영해 문서 근거가 약하거나 일반적인 질문을 줄이고, "
                "직무 관련성, 리스크 검증력, 꼬리질문 연결성을 강화하세요."
            ),
        }
    )


def _fallback_review(question_id: str) -> ReviewResult:
    return ReviewResult(
        question_id=question_id,
        status="rejected",
        reason="질문 검토 결과가 없어 보수적으로 반려 처리했습니다.",
        reject_reason="review_missing",
    )


def _fallback_score(question_id: str) -> ScoreResult:
    return ScoreResult(
        question_id=question_id,
        score=0,
        score_reason="질문 점수 결과가 없어 0점으로 처리했습니다.",
        quality_flags=["SCORE_MISSING"],
    )


def _fallback_answer(question_id: str) -> PredictedAnswer:
    return PredictedAnswer(
        question_id=question_id,
        predicted_answer="문서 근거가 부족하여 현실적인 예상 답변을 생성하지 못했습니다.",
        predicted_answer_basis="predicted_answer_missing",
        answer_confidence="low",
        answer_risk_points=["ANSWER_MISSING"],
    )


def _fallback_follow_up(question_id: str) -> FollowUpQuestion:
    return FollowUpQuestion(
        question_id=question_id,
        follow_up_question="방금 답변하신 내용 중 본인이 직접 수행한 범위와 근거를 구체적으로 설명해주시겠어요?",
        follow_up_basis="follow_up_missing",
        drill_type="역할_검증",
    )


# 여기부터 HR COPILOT AI 노드들 ㅎ

# 초기 상태 구성 노드 - build_state_node
async def build_state_node(state: AgentState) -> AgentState:
    '''
    입력 payload → LLM이 이해 가능한 상태로 변환
    지원자 정보(문서 포함) + 세션 정보 -> 하나의 텍스트로 병합 
    프롬프트 프로필 (채용 기준) 세팅
    재시도(retry) 상태 초기화
    '''
    payload = state.get("source_payload", {})
    candidate_text, has_extracted_text = _merge_document_text(payload)
    prompt_profile = payload.get("prompt_profile") or {}

    recruitment_criteria = {
        "prompt_profile_id": prompt_profile.get("id"),
        "profile_key": prompt_profile.get("profile_key"),
        "target_job": prompt_profile.get("target_job"),
        "system_prompt": prompt_profile.get("system_prompt"),
        "output_schema": prompt_profile.get("output_schema"),
        "has_prompt_profile": bool(prompt_profile),
        "has_extracted_text": has_extracted_text,
    }

    return {
        **state,
        "candidate_text": candidate_text,
        "recruitment_criteria": recruitment_criteria,
        "retry_count": state.get("retry_count", 0),
        "max_retry_count": state.get("max_retry_count", 3),
    }

# 지원자 문서 분석 노드 - analyzer_node
async def analyzer_node(state: AgentState) -> AgentState:
    '''
    지원자 문서 → 구조화된 분석 결과 생성
    LLM 호출 ->
    1. 직무 적합성
    2. 강점 / 약점
    3. 리스크 포인트
    생성
    '''
    result = await _call_structured_output(
        system_prompt=prompts.ANALYZER_SYSTEM_PROMPT,
        user_prompt=prompts.ANALYZER_USER_PROMPT.format(
            candidate_text=state.get("candidate_text", ""),
            recruitment_criteria=_json(state.get("recruitment_criteria", {})),
        ),
        response_model=DocumentAnalysisOutput,
    )
    return {**state, "document_analysis": result.model_dump(mode="json")}

# 면접 질문 생성 노드 - questioner_node
async def questioner_node(state: AgentState) -> AgentState:
    '''
    면접 질문 생성 엔진
    1. 신규 질문 생성
    2. 기존 질문 유지 / 추가 / 재생성
    문서 분석 결과를 기반으로 질문을 생성하며,
    재생성(regenerate) 및 추가 생성(more) 요청을 처리
    '''
    payload = state.get("source_payload", {})
    session = payload.get("session", {})
    existing_questions = state.get("questions", [])
    human_action = state.get("human_action")
    regen_ids = set(state.get("regen_question_ids") or [])

    profile_prompt = (state.get("recruitment_criteria") or {}).get("system_prompt")
    system_prompt = prompts.QUESTIONER_SYSTEM_PROMPT
    if profile_prompt:
        system_prompt = f"{profile_prompt}\n\n{system_prompt}"

    result = await _call_structured_output(
        system_prompt=system_prompt,
        user_prompt=prompts.QUESTIONER_USER_PROMPT.format(
            target_job=session.get("target_job"),
            difficulty_level=session.get("difficulty_level"),
            human_action=human_action,
            additional_instruction=state.get("additional_instruction"),
            regen_question_ids=list(regen_ids),
            candidate_text=state.get("candidate_text", ""),
            document_analysis=_json(state.get("document_analysis", {})),
            existing_questions=_json(
                {
                    "items": existing_questions,
                    "retry_feedback": state.get("retry_feedback"),
                }
            ),
        ),
        response_model=QuestionerOutput,
    )

    new_questions = [
        question.model_dump(mode="json")
        for question in result.questions
    ]
    if human_action == "more_questions":
        questions = existing_questions + new_questions
    elif human_action == "regenerate_question" and regen_ids:
        replacements = {
            question["id"]: question
            for question in new_questions
            if question.get("id") in regen_ids
        }
        replacement_queue = [
            question
            for question in new_questions
            if question.get("id") not in replacements
        ]
        used_replacement_ids: set[str] = set()
        questions = [
            (
                replacements[question.get("id")]
                if question.get("id") in replacements
                else replacement_queue.pop(0)
                if question.get("id") in regen_ids and replacement_queue
                else question
            )
            for question in existing_questions
        ]
        used_replacement_ids.update(replacements)
        missing_replacements = [
            question
            for question in replacement_queue
            if question.get("id") not in used_replacement_ids
        ]
        questions.extend(missing_replacements)
    else:
        questions = new_questions

    normalized_questions = []
    for index, question in enumerate(questions):
        normalized_questions.append({**question, "id": _question_id(question, index)})

    return {
        **state,
        "questions": normalized_questions,
        "candidate_question_count": len(normalized_questions),
    }


async def selector_lite_node(state: AgentState) -> AgentState:
    """
    후속 노드의 처리량을 줄이기 위해 질문 후보 중 5개를 먼저 고른다.
    리뷰/점수 없이 문서 근거, 리스크 검증 질문, 카테고리 다양성을 기준으로 선별한다.
    """
    selected = _select_question_candidates(state.get("questions", []), limit=5)
    return {
        **state,
        "questions": selected,
        "selected_questions": selected,
        "router_decision": "selector_lite",
    }

# 예상 답변 생성 노드 - predictor_node
async def predictor_node(state: AgentState) -> AgentState:
    '''    
    각 질문에 대해 지원자의 예상 답변과
    근거 및 리스크 포인트를 생성
    예상 답변:
    - 근거
    - 리스크 포인트
    - 검증
    '''
    try:
        result = await _call_structured_output(
            system_prompt=prompts.PREDICTOR_SYSTEM_PROMPT,
            user_prompt=prompts.PREDICTOR_USER_PROMPT.format(
                candidate_text=_clip_text(
                    state.get("candidate_text", ""),
                    PREDICTOR_DOCUMENT_CHARS,
                ),
                document_analysis=_json(state.get("document_analysis", {})),
                questions=_json(state.get("questions", [])),
            ),
            response_model=PredictorOutput,
        )
    except Exception as exc:  # noqa: BLE001 - keep graph alive with conservative answers.
        logger.warning("Predictor node failed; using fallback answers: %s", exc)
        fallback_answers = [
            _compact_predicted_answer(
                _fallback_answer(_question_id(question, index)).model_dump(mode="json")
            )
            for index, question in enumerate(state.get("questions", []))
        ]
        return {
            "answers": fallback_answers,
            "node_warnings": [
                {
                    "node": "predictor",
                    "message": "PredictorOutput 생성에 실패해 기본 예상 답변으로 대체했습니다.",
                    "error": str(exc),
                },
            ],
        }

    return {
        "answers": [
            _compact_predicted_answer(answer.model_dump(mode="json"))
            for answer in result.answers
        ],
    }

# 꼬리 질문 생성 노드 - driller_node
async def driller_node(state: AgentState) -> AgentState:
    '''
    심층 검증용 follow-up 질문 생성
    입력데이터:
    1. 생성된 질문 - questions    
    2. 생성된 예상 답변 - answers
    3. 지원자 문서 분석 데이터 - document_analysis
    
    출력데이터:
    1. 꼬리 질문들
    2. 꼬리 질문 타입(역할검증, 경험검증등)
    '''
    try:
        result = await _call_structured_output(
            system_prompt=prompts.DRILLER_SYSTEM_PROMPT,
            user_prompt=prompts.DRILLER_USER_PROMPT.format(
                questions=_json(state.get("questions", [])),
                answers=_json(state.get("answers", [])),
                document_analysis=_json(
                    {
                        "analysis": state.get("document_analysis", {}),
                        "retry_feedback": state.get("retry_feedback"),
                    }
                ),
            ),
            response_model=DrillerOutput,
        )
    except Exception as exc:  # noqa: BLE001 - keep graph alive with conservative follow-ups.
        logger.warning("Driller node failed; using fallback follow-ups: %s", exc)
        fallback_follow_ups = [
            _fallback_follow_up(_question_id(question, index)).model_dump(mode="json")
            for index, question in enumerate(state.get("questions", []))
        ]
        return {
            "follow_ups": fallback_follow_ups,
            "node_warnings": [
                {
                    "node": "driller",
                    "message": "DrillerOutput 생성에 실패해 기본 꼬리 질문으로 대체했습니다.",
                    "error": str(exc),
                },
            ],
        }

    return {
        "follow_ups": [
            follow_up.model_dump(mode="json")
            for follow_up in result.follow_ups
        ],
    }

# 질문 품질 검토 - reviewer_node
async def reviewer_node(state: AgentState) -> AgentState:
    '''
    질문을 사람이 보는 기준으로 평가
    평가기준:
    1. 직무 적합성 
    2. 문서 근거 
    3. 질문 품질
    4. 꼬리 질문 연결성
    
    결과:
    - status: 승인 / 반려
    - reason
    - 수정 권장사항
    '''
    payload = state.get("source_payload", {})
    session = payload.get("session", {})
    try:
        result = await _call_structured_output(
            system_prompt=prompts.REVIEWER_SYSTEM_PROMPT,
            user_prompt=prompts.REVIEWER_USER_PROMPT.format(
                target_job=session.get("target_job"),
                recruitment_criteria=_json(state.get("recruitment_criteria", {})),
                questions=_json(state.get("questions", [])),
                answers=_json(state.get("answers", [])),
                follow_ups=_json(state.get("follow_ups", [])),
            ),
            response_model=ReviewerOutput,
        )
    except Exception as exc:  # noqa: BLE001 - keep graph alive with conservative reviews.
        logger.warning("Reviewer node failed; using fallback reviews: %s", exc)
        fallback_reviews = [
            _fallback_review(_question_id(question, index)).model_dump(mode="json")
            for index, question in enumerate(state.get("questions", []))
        ]
        return {
            "reviews": fallback_reviews,
            "node_warnings": [
                {
                    "node": "reviewer",
                    "message": "ReviewerOutput 생성에 실패해 기본 리뷰로 대체했습니다.",
                    "error": str(exc),
                },
            ],
        }

    return {
        "reviews": [review.model_dump(mode="json") for review in result.reviews],
    }

# 질문 점수화 및 품질 요약 노드 점수화 + 품질 판단 - scorer_node
async def scorer_node(state: AgentState) -> AgentState:
    '''
    정량 평가 + retry 여부 판단 준비
    계산:
    1. 평균점수
    2. 승인/거절 개수
    3. 품질 이슈 추출
    -> reviewer + scorer 결합해서 판단
       router의 입력값 생성
    '''
    try:
        result = await _call_structured_output(
            system_prompt=prompts.SCORER_SYSTEM_PROMPT,
            user_prompt=prompts.SCORER_USER_PROMPT.format(
                questions=_json(state.get("questions", [])),
                answers=_json(state.get("answers", [])),
                follow_ups=_json(state.get("follow_ups", [])),
                reviews=_json(state.get("reviews", [])),
            ),
            response_model=ScorerOutput,
        )
        scores = [score.model_dump(mode="json") for score in result.scores]
        node_warnings: list[dict[str, Any]] = []
    except Exception as exc:  # noqa: BLE001 - keep graph alive with conservative scores.
        logger.warning("Scorer node failed; using fallback scores: %s", exc)
        scores = [
            _fallback_score(_question_id(question, index)).model_dump(mode="json")
            for index, question in enumerate(state.get("questions", []))
        ]
        node_warnings = [
            {
                "node": "scorer",
                "message": "ScorerOutput 생성에 실패해 기본 점수로 대체했습니다.",
                "error": str(exc),
            },
        ]
    reviews = state.get("reviews", [])
    approved_count = sum(1 for review in reviews if _is_approved_review(review))
    rejected_count = sum(1 for review in reviews if review.get("status") == "rejected")
    avg_score = (
        sum(score.get("score", 0) for score in scores) / len(scores)
        if scores
        else 0
    )
    quality_issue_set = {
        flag
        for score in scores
        for flag in score.get("quality_flags", [])
    }
    if any(not _is_approved_review(review) for review in reviews):
        quality_issue_set.add("REVIEW_NOT_APPROVED")
    if any(score.get("score", 0) < 80 for score in scores):
        quality_issue_set.add("LOW_SCORE")
    if any(flag in FOLLOW_UP_WEAK_FLAGS for flag in quality_issue_set):
        quality_issue_set.add("FOLLOW_UP_TOO_WEAK")
    if any(flag in QUESTION_REWRITE_FLAGS for flag in quality_issue_set):
        quality_issue_set.add("QUESTION_REWRITE_NEEDED")
    quality_issues = sorted(quality_issue_set)

    update: dict[str, Any] = {
        "scores": scores,
        "review_summary": {
            "approved_count": approved_count,
            "rejected_count": rejected_count,
            "avg_score": round(avg_score, 2),
            "quality_issues": quality_issues,
        },
    }
    if node_warnings:
        update["node_warnings"] = node_warnings
    return update

"""
질문 재생성 retry 노드.

retry_count를 증가시키고,
questioner 재실행을 위한 피드백을 생성한다.
"""
async def increment_retry_for_questioner_node(state: AgentState) -> AgentState:
    return {
        **state,
        "retry_count": state.get("retry_count", 0) + 1,
        "router_decision": "questioner",
        "retry_feedback": _build_retry_feedback(state),
    }

"""
꼬리질문 재생성 retry 노드.

retry_count를 증가시키고,
driller 재실행을 위한 피드백을 생성한다.
"""
async def increment_retry_for_driller_node(state: AgentState) -> AgentState:
    return {
        **state,
        "retry_count": state.get("retry_count", 0) + 1,
        "router_decision": "driller",
        "retry_feedback": _build_retry_feedback(state),
    }

"""
최종 질문 선택 노드.

리뷰 및 점수를 기반으로 중복 제거,
카테고리 균형을 고려하여 최종 질문을 선택한다.
"""
async def selector_node(state: AgentState) -> AgentState:
    reviews_by_id = {
        review.get("question_id"): review
        for review in state.get("reviews", [])
    }
    scores_by_id = {
        score.get("question_id"): score
        for score in state.get("scores", [])
    }
    selected = _select_question_candidates(
        state.get("questions", []),
        reviews_by_id=reviews_by_id,
        scores_by_id=scores_by_id,
        limit=5,
    )

    return {
        "selected_questions": selected,
        "router_decision": state.get("router_decision") or "selector",
    }

# 최종 응답 생성
async def final_formatter_node(state: AgentState) -> AgentState:
    '''
    모든 결과를 API 응답 형태로 변환
    포함내용:
    1. 질문
    2. 예상 답변
    3. 꼬리 질문
    4. 리뷰
    5. 점수
    
    fallback : 데이터 없으면 자동 보완
    _fallback_answer
    _fallback_review
    _fallback_score
    
    상태 결정
    status:
    - completed
    - partial_completed
    '''
    payload = state.get("source_payload", {})
    session = payload.get("session", {})
    candidate = payload.get("candidate", {})
    selected_questions = state.get("selected_questions", [])
    answers = state.get("answers", [])
    follow_ups = state.get("follow_ups", [])
    reviews = state.get("reviews", [])
    scores = state.get("scores", [])

    items: list[InterviewQuestionItem] = []
    for index, question in enumerate(selected_questions):
        question_id = _question_id(question, index)
        answer = PredictedAnswer.model_validate(
            _find_by_question_id(answers, question_id) or _fallback_answer(question_id)
        )
        follow_up = FollowUpQuestion.model_validate(
            _find_by_question_id(follow_ups, question_id)
            or _fallback_follow_up(question_id)
        )
        review = ReviewResult.model_validate(
            _find_by_question_id(reviews, question_id) or _fallback_review(question_id)
        )
        score = ScoreResult.model_validate(
            _find_by_question_id(scores, question_id) or _fallback_score(question_id)
        )
        question_model = QuestionCandidate.model_validate(question)

        items.append(
            InterviewQuestionItem(
                id=question_id,
                category=question_model.category,
                question_text=question_model.question_text,
                generation_basis=question_model.generation_basis,
                document_evidence=question_model.document_evidence,
                evaluation_guide=question_model.evaluation_guide,
                predicted_answer=answer.predicted_answer,
                predicted_answer_basis=answer.predicted_answer_basis,
                follow_up_question=follow_up.follow_up_question,
                follow_up_basis=follow_up.follow_up_basis,
                risk_tags=question_model.risk_tags,
                competency_tags=question_model.competency_tags,
                review=review,
                score=score.score,
                score_reason=score.score_reason,
            )
        )

    analysis = DocumentAnalysisOutput.model_validate(
        state.get("document_analysis")
        or {
            "job_fit": "분석 결과가 없어 직무 적합성을 판단하지 못했습니다.",
        }
    )
    has_extracted_text = (state.get("recruitment_criteria") or {}).get(
        "has_extracted_text",
        False,
    )
    approved_count = sum(1 for item in items if item.review.status == "approved")
    is_partial = (
        not has_extracted_text
        or len(items) < 5
        or approved_count < 5
        or state.get("retry_count", 0) >= state.get("max_retry_count", 3)
        or bool(state.get("node_warnings"))
    )

    response = QuestionGenerationResponse(
        session_id=session.get("session_id"),
        candidate_id=candidate.get("candidate_id"),
        target_job=session.get("target_job"),
        difficulty_level=session.get("difficulty_level"),
        status="partial_completed" if is_partial else "completed",
        analysis_summary=analysis,
        questions=items,
        generation_metadata={
            "total_candidate_questions": state.get(
                "candidate_question_count",
                len(state.get("questions", [])),
            ),
            "selected_question_count": len(items),
            "retry_count": state.get("retry_count", 0),
            "router_decision": state.get("router_decision", "selector"),
            "is_all_approved": bool(items) and approved_count == len(items),
            "review_summary": state.get("review_summary", {}),
            "node_warnings": state.get("node_warnings", []),
        },
    )

    return {"final_response": response.model_dump(mode="json")}
