import asyncio
import json
import logging
from typing import Any, TypeVar

from pydantic import BaseModel

from ai.interview_graph.llm_usage import StructuredOutputCallError
from ai.interview_graph_JY.jy_structured_output import call_structured_output_with_model
from ai.interview_graph_JY.model_routing import resolve_model
from ai.interview_graph_JY.schemas import (
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
)
from ai.interview_graph_JY import prompts
from ai.interview_graph_JY.router import route_after_review
from ai.interview_graph_JY.state import AgentState

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

MAX_DOCUMENT_CHARS = 18000
PREDICTOR_DOCUMENT_CHARS = 7000
LOW_SCORE_THRESHOLD = 80
QUESTIONER_RETRY_TARGET_LIMIT = 2
REVIEW_SCORE_BASE = {"approved": 38, "needs_revision": 20, "rejected": 0}
ANALYZER_RISK_LIMIT = 6
ANALYZER_EVIDENCE_LIMIT = 5
ANALYZER_QUESTION_POINT_LIMIT = 8
QUESTION_COUNT = 8
QUESTION_TEXT_CHARS = 180
QUESTION_BASIS_CHARS = 140
QUESTION_EVIDENCE_LIMIT = 2
QUESTION_EVIDENCE_CHARS = 140
QUESTION_EVALUATION_GUIDE_CHARS = 180
QUESTION_TAG_LIMIT = 4

DRILLER_CONCURRENCY = 3


async def _call_structured_output(
    *,
    node_name: str,
    system_prompt: str,
    user_prompt: str,
    response_model: type[T],
) -> tuple[T, list[dict[str, Any]]]:
    return await call_structured_output_with_model(
        node_name=node_name,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_model=response_model,
        model_name=resolve_model(node_name),
    )


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _clip(value: str, max_chars: int) -> str:
    text = value.strip()
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars]}\n\n...(길이 제한으로 일부 생략)"


def _truncate(value: Any, max_chars: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _truncate_list(values: Any, *, limit: int, max_chars: int) -> list[str]:
    if not isinstance(values, list):
        values = [values] if _has_text(values) else []
    return [
        truncated
        for truncated in (_truncate(value, max_chars) for value in values[:limit])
        if truncated
    ]


def _question_id(question: dict[str, Any], index: int) -> str:
    value = str(question.get("id") or "").strip()
    return value or f"jy-q-{index + 1:03d}"


def _has_text(value: Any) -> bool:
    return bool(str(value or "").strip())


def _has_items(value: Any) -> bool:
    if isinstance(value, list):
        return any(_has_text(item) for item in value)
    return _has_text(value)


def _compact_document_evidence(item: Any) -> dict[str, Any]:
    if hasattr(item, "model_dump"):
        item = item.model_dump(mode="json")
    if not isinstance(item, dict):
        return {"quote": _truncate(item, 120), "reason": ""}
    return {
        "document_id": item.get("document_id"),
        "document_type": item.get("document_type"),
        "title": _truncate(item.get("title"), 80),
        "quote": _truncate(item.get("quote"), 120),
        "reason": _truncate(item.get("reason"), 120),
    }


def _compact_document_analysis(analysis: dict[str, Any]) -> dict[str, Any]:
    evidence = [
        compact
        for compact in (
            _compact_document_evidence(item)
            for item in list(analysis.get("document_evidence") or [])[:ANALYZER_EVIDENCE_LIMIT]
        )
        if compact.get("quote") or compact.get("reason")
    ]
    return {
        "strengths": [],
        "weaknesses": [],
        "risks": _truncate_list(
            analysis.get("risks", []),
            limit=ANALYZER_RISK_LIMIT,
            max_chars=100,
        ),
        "document_evidence": evidence,
        "job_fit": _truncate(analysis.get("job_fit"), 220),
        "questionable_points": _truncate_list(
            analysis.get("questionable_points", []),
            limit=ANALYZER_QUESTION_POINT_LIMIT,
            max_chars=120,
        ),
    }


def _compact_question(question: dict[str, Any]) -> dict[str, Any]:
    return {
        **question,
        "question_text": _truncate(question.get("question_text"), QUESTION_TEXT_CHARS),
        "generation_basis": _truncate(question.get("generation_basis"), QUESTION_BASIS_CHARS),
        "document_evidence": _truncate_list(
            question.get("document_evidence", []),
            limit=QUESTION_EVIDENCE_LIMIT,
            max_chars=QUESTION_EVIDENCE_CHARS,
        ),
        "evaluation_guide": _truncate(
            question.get("evaluation_guide"),
            QUESTION_EVALUATION_GUIDE_CHARS,
        ),
        "risk_tags": _truncate_list(
            question.get("risk_tags", []),
            limit=QUESTION_TAG_LIMIT,
            max_chars=40,
        ),
        "competency_tags": _truncate_list(
            question.get("competency_tags", []),
            limit=QUESTION_TAG_LIMIT,
            max_chars=40,
        ),
    }


def _is_risk_question(question: dict[str, Any]) -> bool:
    return question.get("category") in {"RISK", "리스크"} or bool(question.get("risk_tags"))


def _is_approved(review: dict[str, Any]) -> bool:
    return review.get("status") == "approved"


def _select_question_candidates(
    questions: list[dict[str, Any]],
    *,
    reviews_by_id: dict[str, dict[str, Any]] | None = None,
    scores_by_id: dict[str, dict[str, Any]] | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    reviews_by_id = reviews_by_id or {}
    scores_by_id = scores_by_id or {}

    unique: list[dict[str, Any]] = []
    seen_texts: set[str] = set()
    for question in questions:
        text_key = " ".join(str(question.get("question_text") or "").split()).lower()
        if not text_key or text_key in seen_texts:
            continue
        seen_texts.add(text_key)
        unique.append(question)

    ranked = sorted(
        unique,
        key=lambda question: (
            _is_approved(reviews_by_id.get(str(question.get("id")), {})),
            scores_by_id.get(str(question.get("id")), {}).get("score", 0),
            _is_risk_question(question),
            bool(question.get("document_evidence")),
        ),
        reverse=True,
    )

    selected: list[dict[str, Any]] = []
    risk_question = next((question for question in ranked if _is_risk_question(question)), None)
    if risk_question:
        selected.append(risk_question)
    for question in ranked:
        if len(selected) >= limit:
            break
        if question not in selected:
            selected.append(question)
    return selected


def _merge_document_text(state: AgentState) -> tuple[str, bool]:
    sections = [
        "[Session]",
        f"session_id: {state.get('session_id')}",
        f"target_job: {state.get('target_job')}",
        f"difficulty_level: {state.get('difficulty_level')}",
        "",
        "[Candidate]",
        f"candidate_id: {state.get('candidate_id')}",
        f"name: {state.get('candidate_name')}",
    ]
    documents = list(state.get("documents") or [])
    has_text = False
    per_doc_budget = max(800, MAX_DOCUMENT_CHARS // max(1, len(documents)))

    for document in documents:
        extracted_text = str(document.get("extracted_text") or "").strip()
        has_text = has_text or bool(extracted_text)
        sections.extend(
            [
                "",
                "[Document]",
                f"document_id: {document.get('document_id')}",
                f"document_type: {document.get('document_type')}",
                f"title: {document.get('title')}",
                "extracted_text:",
                extracted_text[:per_doc_budget] or "(no extracted text)",
            ]
        )

    return "\n".join(sections)[:MAX_DOCUMENT_CHARS], has_text


def _recruitment_context(state: AgentState) -> dict[str, Any]:
    profile = state.get("prompt_profile") or {}
    return {
        "target_job": state.get("target_job"),
        "profile_key": profile.get("profile_key"),
        "profile_target_job": profile.get("target_job"),
        "system_prompt": profile.get("system_prompt"),
        "output_schema": profile.get("output_schema"),
    }


def _replace_questions_by_id(
    current: list[dict[str, Any]],
    replacements: list[dict[str, Any]],
    target_question_ids: list[str],
) -> list[dict[str, Any]]:
    if not current or not replacements or not target_question_ids:
        return replacements or current
    replacement_by_id = {
        question_id: {**replacement, "id": question_id}
        for question_id, replacement in zip(target_question_ids, replacements, strict=False)
    }
    seen_ids = {str(question.get("id")) for question in current}
    merged = [replacement_by_id.get(str(question.get("id")), question) for question in current]
    merged.extend(
        replacement
        for question_id, replacement in replacement_by_id.items()
        if question_id not in seen_ids
    )
    return merged


def _target_question_ids(state: AgentState) -> list[str]:
    seen: set[str] = set()
    target_ids: list[str] = []
    for item in state.get("target_question_ids", []) or []:
        question_id = str(item).strip()
        if question_id and question_id not in seen:
            target_ids.append(question_id)
            seen.add(question_id)
    return target_ids


def _questions_for_targets(
    questions: list[dict[str, Any]],
    target_question_ids: list[str],
) -> list[dict[str, Any]]:
    if not target_question_ids:
        return questions
    target_set = set(target_question_ids)
    return [
        {**question, "id": _question_id(question, index)}
        for index, question in enumerate(questions)
        if _question_id(question, index) in target_set
    ]


def _items_for_question_ids(
    items: list[dict[str, Any]],
    question_ids: list[str],
) -> list[dict[str, Any]]:
    if not question_ids:
        return items
    target_set = set(question_ids)
    return [item for item in items if str(item.get("question_id")) in target_set]


def _merge_items_by_question_id(
    current: list[dict[str, Any]],
    replacements: list[dict[str, Any]],
    target_question_ids: list[str],
) -> list[dict[str, Any]]:
    if not target_question_ids:
        return replacements

    target_set = set(target_question_ids)
    replacement_by_id = {
        str(item.get("question_id")): item
        for item in replacements
        if item.get("question_id")
    }
    merged: list[dict[str, Any]] = []
    used_ids: set[str] = set()
    for item in current:
        question_id = str(item.get("question_id"))
        if question_id in target_set:
            replacement = replacement_by_id.get(question_id)
            if replacement:
                merged.append(replacement)
                used_ids.add(question_id)
            continue
        merged.append(item)
    merged.extend(
        replacement
        for question_id, replacement in replacement_by_id.items()
        if question_id not in used_ids
    )
    return merged


def _find_by_question_id(items: list[dict[str, Any]], question_id: str) -> dict[str, Any]:
    return next((item for item in items if item.get("question_id") == question_id), {})


def _fallback_answer(question_id: str) -> PredictedAnswer:
    return PredictedAnswer(
        question_id=question_id,
        predicted_answer="문서 근거가 부족하여 현실적인 예상 답변을 확정하기 어렵습니다.",
        predicted_answer_basis="Predictor 결과가 없어 기본 예상 답변을 사용했습니다.",
        answer_confidence="low",
        answer_risk_points=["예상답변_누락"],
    )


def _fallback_follow_up(question_id: str) -> FollowUpQuestion:
    return FollowUpQuestion(
        question_id=question_id,
        follow_up_question="방금 답변하신 내용에서 본인이 직접 맡은 역할과 판단 근거를 더 구체적으로 설명해주시겠어요?",
        follow_up_basis="Driller 결과가 없어 역할 검증형 기본 꼬리질문을 사용했습니다.",
        drill_type="역할_검증",
    )


def _fallback_review(question_id: str) -> ReviewResult:
    return ReviewResult(
        question_id=question_id,
        status="needs_revision",
        reason="Reviewer 결과가 없어 수동 검토가 필요합니다.",
        reject_reason="review_missing",
        recommended_revision="문서 근거, 직무 관련성, 평가 가이드 구체성을 다시 확인하세요.",
    )


def _fallback_score(question_id: str) -> ScoreResult:
    return ScoreResult(
        question_id=question_id,
        score=0,
        score_reason="점수 결과가 없어 0점으로 처리했습니다.",
        quality_flags=["SCORE_MISSING"],
    )


async def build_state_node(state: AgentState) -> dict[str, Any]:
    candidate_context, has_extracted_text = _merge_document_text(state)
    warnings = []
    if not has_extracted_text:
        warnings.append(
            {
                "node": "build_state",
                "message": "추출된 문서 텍스트가 없어 세션/지원자 메타데이터 중심으로 질문을 생성합니다.",
            }
        )
    return {
        "candidate_context": candidate_context,
        "retry_count": state.get("retry_count", 0),
        "max_retry_count": state.get("max_retry_count", 2),
        "node_warnings": warnings,
    }


async def analyzer_node(state: AgentState) -> dict[str, Any]:
    result, llm_usages = await _call_structured_output(
        node_name="jy_analyzer",
        system_prompt=prompts.ANALYZER_SYSTEM_PROMPT,
        user_prompt=prompts.ANALYZER_USER_PROMPT.format(
            candidate_context=state.get("candidate_context", ""),
            recruitment_criteria=_json(_recruitment_context(state)),
        ),
        response_model=DocumentAnalysisOutput,
    )
    return {
        "document_analysis": _compact_document_analysis(result.model_dump(mode="json")),
        "llm_usages": llm_usages,
    }


async def questioner_node(state: AgentState) -> dict[str, Any]:
    target_question_ids = _target_question_ids(state)
    human_action = state.get("human_action")
    is_partial_regeneration = human_action == "regenerate_question" and bool(target_question_ids)
    question_count_instruction = "- 최종 후보 질문은 8개 생성하세요."
    expected_question_count = QUESTION_COUNT
    if is_partial_regeneration:
        expected_question_count = len(target_question_ids)
        question_count_instruction = (
            f"- 재생성 대상 ID 수에 맞춰 질문은 정확히 {len(target_question_ids)}개 생성하세요."
        )

    profile_prompt = (state.get("prompt_profile") or {}).get("system_prompt")
    system_prompt = prompts.QUESTIONER_SYSTEM_PROMPT
    if profile_prompt:
        system_prompt = f"{profile_prompt}\n\n{system_prompt}"

    result, llm_usages = await _call_structured_output(
        node_name="jy_questioner",
        system_prompt=system_prompt,
        user_prompt=prompts.QUESTIONER_USER_PROMPT.format(
            question_count_instruction=question_count_instruction,
            target_job=state.get("target_job"),
            difficulty_level=state.get("difficulty_level"),
            human_action=human_action,
            additional_instruction=state.get("additional_instruction"),
            target_question_ids=target_question_ids,
            candidate_context=state.get("candidate_context", ""),
            document_analysis=_json(
                _compact_document_analysis(state.get("document_analysis", {}))
            ),
            existing_questions=_json(
                {
                    "questions": [
                        _compact_question(question)
                        for question in state.get("questions", [])
                        if (not is_partial_regeneration)
                        or (_question_id(question, 0) not in set(target_question_ids))
                    ],
                    "retry_feedback": state.get("retry_feedback"),
                }
            ),
        ),
        response_model=QuestionerOutput,
    )

    generated = [
        _compact_question(
            {
                **question.model_dump(mode="json"),
                "id": _question_id(question.model_dump(mode="json"), index),
            }
        )
        for index, question in enumerate(result.questions[:expected_question_count])
    ]
    if is_partial_regeneration:
        questions = _replace_questions_by_id(state.get("questions", []), generated, target_question_ids)
    else:
        questions = generated
    update = {
        "questions": questions,
        "human_action": None,
        "target_question_ids": target_question_ids if is_partial_regeneration else [],
        "llm_usages": llm_usages,
    }
    if is_partial_regeneration:
        update.update(
            {
                "answers": state.get("answers", []),
                "follow_ups": state.get("follow_ups", []),
                "reviews": state.get("reviews", []),
                "scores": state.get("scores", []),
            }
        )
    else:
        update.update({"answers": [], "follow_ups": [], "reviews": [], "scores": []})
    return update


async def selector_lite_node(state: AgentState) -> dict[str, Any]:
    """
    비싼 Predictor/Driller/Reviewer 호출 전에 최종 후보 규모로 먼저 줄인다.
    최종 selector는 리뷰/점수를 반영해 다시 정렬한다.
    """
    return {
        "questions": _select_question_candidates(state.get("questions", []), limit=5),
        "llm_usages": [],
    }


async def predictor_node(state: AgentState) -> dict[str, Any]:
    target_question_ids = _target_question_ids(state)
    questions = state.get("questions", [])
    scoped_questions = _questions_for_targets(questions, target_question_ids)
    if target_question_ids and not scoped_questions:
        return {
            "answers": state.get("answers", []),
            "llm_usages": [],
            "node_warnings": [
                {
                    "node": "jy_predictor",
                    "message": "부분 재생성 대상 질문을 찾지 못해 기존 예상 답변을 유지했습니다.",
                }
            ],
        }
    try:
        result, llm_usages = await _call_structured_output(
            node_name="jy_predictor",
            system_prompt=prompts.PREDICTOR_SYSTEM_PROMPT,
            user_prompt=prompts.PREDICTOR_USER_PROMPT.format(
                candidate_context=_clip(state.get("candidate_context", ""), PREDICTOR_DOCUMENT_CHARS),
                document_analysis=_json(
                    _compact_document_analysis(state.get("document_analysis", {}))
                ),
                questions=_json(scoped_questions),
            ),
            response_model=PredictorOutput,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("JY predictor failed; using fallback answers: %s", exc)
        usages = exc.usages if isinstance(exc, StructuredOutputCallError) else []
        fallback_answers = [
            _fallback_answer(_question_id(question, index)).model_dump(mode="json")
            for index, question in enumerate(scoped_questions)
        ]
        return {
            "answers": _merge_items_by_question_id(
                state.get("answers", []),
                fallback_answers,
                target_question_ids,
            ),
            "llm_usages": usages,
            "node_warnings": [{"node": "jy_predictor", "message": str(exc)}],
        }
    answers = [answer.model_dump(mode="json") for answer in result.answers]
    return {
        "answers": _merge_items_by_question_id(
            state.get("answers", []),
            answers,
            target_question_ids,
        ),
        "llm_usages": llm_usages,
    }


async def driller_node(state: AgentState) -> dict[str, Any]:
    target_question_ids = _target_question_ids(state)
    questions = state.get("questions", [])
    scoped_questions = _questions_for_targets(questions, target_question_ids)
    scoped_question_ids = [
        _question_id(question, index)
        for index, question in enumerate(scoped_questions)
    ]
    scoped_answers = _items_for_question_ids(state.get("answers", []), scoped_question_ids)
    if target_question_ids and not scoped_questions:
        return {
            "follow_ups": state.get("follow_ups", []),
            "llm_usages": [],
            "node_warnings": [
                {
                    "node": "jy_driller",
                    "message": "부분 재생성 대상 질문을 찾지 못해 기존 꼬리질문을 유지했습니다.",
                }
            ],
        }
    try:
        document_analysis = _json(
            {
                "document_analysis": _compact_document_analysis(
                    state.get("document_analysis", {})
                ),
                "retry_feedback": state.get("retry_feedback"),
            }
        )
        answer_by_question_id = {
            str(answer.get("question_id")): answer
            for answer in scoped_answers
            if answer.get("question_id")
        }
        semaphore = asyncio.Semaphore(DRILLER_CONCURRENCY)

        async def call_single_driller(
            question: dict[str, Any],
            question_id: str,
        ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
            async with semaphore:
                answer = answer_by_question_id.get(question_id) or _fallback_answer(
                    question_id
                ).model_dump(mode="json")
                try:
                    result, usages = await _call_structured_output(
                        node_name="jy_driller",
                        system_prompt=prompts.DRILLER_SYSTEM_PROMPT,
                        user_prompt=prompts.DRILLER_USER_PROMPT.format(
                            questions=_json([{**question, "id": question_id}]),
                            answers=_json([answer]),
                            document_analysis=document_analysis,
                        ),
                        response_model=DrillerOutput,
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "JY driller failed for question_id=%s; using fallback follow-up: %s",
                        question_id,
                        exc,
                    )
                    usages = exc.usages if isinstance(exc, StructuredOutputCallError) else []
                    return (
                        [_fallback_follow_up(question_id).model_dump(mode="json")],
                        usages,
                        [
                            {
                                "node": "jy_driller",
                                "message": f"{question_id}: {exc}",
                            }
                        ],
                    )

                follow_ups = [item.model_dump(mode="json") for item in result.follow_ups]
                follow_up = _find_by_question_id(follow_ups, question_id)
                if not follow_up and follow_ups:
                    follow_up = {**follow_ups[0], "question_id": question_id}
                if not follow_up:
                    return (
                        [_fallback_follow_up(question_id).model_dump(mode="json")],
                        usages,
                        [
                            {
                                "node": "jy_driller",
                                "message": f"{question_id}: Driller가 꼬리질문을 반환하지 않아 fallback을 사용했습니다.",
                            }
                        ],
                    )
                return ([follow_up], usages, [])

        driller_results = await asyncio.gather(
            *(
                call_single_driller(question, question_id)
                for question, question_id in zip(
                    scoped_questions,
                    scoped_question_ids,
                    strict=False,
                )
            )
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("JY driller failed; using fallback follow-ups: %s", exc)
        usages = exc.usages if isinstance(exc, StructuredOutputCallError) else []
        fallback_follow_ups = [
            _fallback_follow_up(_question_id(question, index)).model_dump(mode="json")
            for index, question in enumerate(scoped_questions)
        ]
        return {
            "follow_ups": _merge_items_by_question_id(
                state.get("follow_ups", []),
                fallback_follow_ups,
                target_question_ids,
            ),
            "llm_usages": usages,
            "node_warnings": [{"node": "jy_driller", "message": str(exc)}],
        }
    follow_ups = [
        follow_up
        for result_follow_ups, _, _ in driller_results
        for follow_up in result_follow_ups
    ]
    llm_usages = [
        usage
        for _, result_usages, _ in driller_results
        for usage in result_usages
    ]
    warnings = [
        warning
        for _, _, result_warnings in driller_results
        for warning in result_warnings
    ]
    return {
        "follow_ups": _merge_items_by_question_id(
            state.get("follow_ups", []),
            follow_ups,
            target_question_ids,
        ),
        "llm_usages": llm_usages,
        "node_warnings": warnings,
    }


async def reviewer_node(state: AgentState) -> dict[str, Any]:
    target_question_ids = _target_question_ids(state)
    questions = state.get("questions", [])
    scoped_questions = _questions_for_targets(questions, target_question_ids)
    scoped_question_ids = [
        _question_id(question, index)
        for index, question in enumerate(scoped_questions)
    ]
    scoped_answers = _items_for_question_ids(state.get("answers", []), scoped_question_ids)
    scoped_follow_ups = _items_for_question_ids(state.get("follow_ups", []), scoped_question_ids)
    if target_question_ids and not scoped_questions:
        return {
            "reviews": state.get("reviews", []),
            "llm_usages": [],
            "node_warnings": [
                {
                    "node": "jy_reviewer",
                    "message": "부분 재생성 대상 질문을 찾지 못해 기존 리뷰를 유지했습니다.",
                }
            ],
        }
    try:
        result, llm_usages = await _call_structured_output(
            node_name="jy_reviewer",
            system_prompt=prompts.REVIEWER_SYSTEM_PROMPT,
            user_prompt=prompts.REVIEWER_USER_PROMPT.format(
                target_job=state.get("target_job"),
                recruitment_criteria=_json(_recruitment_context(state)),
                questions=_json(scoped_questions),
                answers=_json(scoped_answers),
                follow_ups=_json(scoped_follow_ups),
            ),
            response_model=ReviewerOutput,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("JY reviewer failed; using fallback reviews: %s", exc)
        usages = exc.usages if isinstance(exc, StructuredOutputCallError) else []
        fallback_reviews = [
            _fallback_review(_question_id(question, index)).model_dump(mode="json")
            for index, question in enumerate(scoped_questions)
        ]
        return {
            "reviews": _merge_items_by_question_id(
                state.get("reviews", []),
                fallback_reviews,
                target_question_ids,
            ),
            "llm_usages": usages,
            "node_warnings": [{"node": "jy_reviewer", "message": str(exc)}],
        }
    reviews = [review.model_dump(mode="json") for review in result.reviews]
    return {
        "reviews": _merge_items_by_question_id(
            state.get("reviews", []),
            reviews,
            target_question_ids,
        ),
        "llm_usages": llm_usages,
    }


def _score_question(
    *,
    question: dict[str, Any],
    review: dict[str, Any],
    answer: dict[str, Any],
    follow_up: dict[str, Any],
    duplicate: bool,
) -> ScoreResult:
    status = str(review.get("status") or "rejected")
    score = REVIEW_SCORE_BASE.get(status, 0)
    flags: list[str] = []
    reasons: list[str] = []

    if status == "approved":
        reasons.append("Reviewer가 사용 가능으로 판단했습니다")
    else:
        flags.append("REVIEW_NOT_APPROVED")
        reasons.append("Reviewer가 수정 또는 반려로 판단했습니다")

    if _has_items(question.get("document_evidence")):
        score += 20
    else:
        flags.append("EVIDENCE_TOO_WEAK")
    if _has_text(question.get("evaluation_guide")):
        score += 12
    else:
        flags.append("EVALUATION_GUIDE_TOO_WEAK")
    if _has_items(question.get("competency_tags")):
        score += 10
    else:
        flags.append("LOW_JOB_RELEVANCE")
    if _is_risk_question(question):
        score += 10
    if _has_text(answer.get("predicted_answer")):
        score += 5
    if _has_text(follow_up.get("follow_up_question")):
        score += 5
    else:
        flags.append("FOLLOW_UP_TOO_WEAK")
    if duplicate:
        score -= 15
        flags.append("DUPLICATE_RISK")
    if _has_text(review.get("reject_reason")):
        score -= 10
    score = max(0, min(100, score))
    if score < LOW_SCORE_THRESHOLD:
        flags.append("LOW_SCORE")

    unique_flags = sorted(set(flags))
    if unique_flags:
        reasons.append(f"보완 신호: {', '.join(unique_flags)}")
    else:
        reasons.append("문서 근거, 직무 관련성, 면접 사용성이 균형 있게 충족되었습니다")

    return ScoreResult(
        question_id=str(question.get("id")),
        score=score,
        score_reason="; ".join(reasons),
        quality_flags=unique_flags,
    )


async def scorer_node(state: AgentState) -> dict[str, Any]:
    questions = list(state.get("questions", []))
    reviews_by_id = {str(item.get("question_id")): item for item in state.get("reviews", [])}
    answers_by_id = {str(item.get("question_id")): item for item in state.get("answers", [])}
    follow_ups_by_id = {str(item.get("question_id")): item for item in state.get("follow_ups", [])}

    seen_texts: dict[str, str] = {}
    duplicate_ids: set[str] = set()
    for index, question in enumerate(questions):
        question_id = _question_id(question, index)
        question["id"] = question_id
        text_key = " ".join(str(question.get("question_text") or "").split()).lower()
        if text_key in seen_texts:
            duplicate_ids.add(question_id)
            duplicate_ids.add(seen_texts[text_key])
        elif text_key:
            seen_texts[text_key] = question_id

    scores = [
        _score_question(
            question=question,
            review=reviews_by_id.get(_question_id(question, index), {}),
            answer=answers_by_id.get(_question_id(question, index), {}),
            follow_up=follow_ups_by_id.get(_question_id(question, index), {}),
            duplicate=_question_id(question, index) in duplicate_ids,
        ).model_dump(mode="json")
        for index, question in enumerate(questions)
    ]
    approved_count = sum(1 for review in state.get("reviews", []) if _is_approved(review))
    low_score_ids = [str(score["question_id"]) for score in scores if score["score"] < LOW_SCORE_THRESHOLD]
    quality_issues = sorted({flag for score in scores for flag in score.get("quality_flags", [])})
    avg_score = round(sum(score["score"] for score in scores) / len(scores), 2) if scores else 0
    review_summary = {
        "approved_count": approved_count,
        "low_score_count": len(low_score_ids),
        "low_score_question_ids": low_score_ids,
        "avg_score": avg_score,
        "quality_issues": quality_issues,
        "scored_question_count": len(scores),
    }
    router_decision = route_after_review(
        {
            **state,
            "questions": questions,
            "scores": scores,
            "review_summary": review_summary,
        }
    )
    return {
        "questions": questions,
        "scores": scores,
        "review_summary": review_summary,
        "router_decision": router_decision,
        "llm_usages": [],
    }


def _retry_feedback(state: AgentState) -> str:
    summary = state.get("review_summary", {})
    low_score_ids = [
        str(item)
        for item in (summary or {}).get("low_score_question_ids", [])
        if item
    ][:QUESTIONER_RETRY_TARGET_LIMIT]
    low_score_id_set = set(low_score_ids)
    reviews = state.get("reviews", [])
    scores = state.get("scores", [])
    if low_score_id_set:
        reviews = [
            review
            for review in reviews
            if str(review.get("question_id")) in low_score_id_set
        ]
        scores = [
            score
            for score in scores
            if str(score.get("question_id")) in low_score_id_set
        ]
    return _json(
        {
            "instruction": "낮은 점수 또는 미승인 질문의 문서 근거, 직무 관련성, 꼬리질문 연결성을 보완하세요.",
            "review_summary": summary,
            "reviews": reviews[:5],
            "scores": scores[:5],
        }
    )


def _retry_target_question_ids(state: AgentState) -> list[str]:
    """
    재시도 시 전체 질문을 재생성하지 않도록, "고치면 효과가 큰" 질문 ID를 최대 2개 선택한다.
    우선순위: low_score_question_ids -> (점수 오름차순) -> (미승인 리뷰) -> (앞쪽 2개)
    """
    summary = state.get("review_summary", {}) or {}
    low_score_ids = [
        str(item)
        for item in (summary.get("low_score_question_ids", []) or [])
        if item
    ]
    target_ids = [qid for qid in low_score_ids if qid][:QUESTIONER_RETRY_TARGET_LIMIT]
    if target_ids:
        return target_ids

    scores = list(state.get("scores", []) or [])
    scored = [
        (str(item.get("question_id")), int(item.get("score", 0) or 0))
        for item in scores
        if item.get("question_id")
    ]
    scored.sort(key=lambda pair: pair[1])
    for qid, _ in scored:
        if qid and qid not in target_ids:
            target_ids.append(qid)
        if len(target_ids) >= QUESTIONER_RETRY_TARGET_LIMIT:
            return target_ids

    reviews = list(state.get("reviews", []) or [])
    for review in reviews:
        qid = str(review.get("question_id") or "").strip()
        if not qid or qid in target_ids:
            continue
        if str(review.get("status") or "") != "approved":
            target_ids.append(qid)
        if len(target_ids) >= QUESTIONER_RETRY_TARGET_LIMIT:
            return target_ids

    for question in state.get("questions", []) or []:
        qid = str(question.get("id") or "").strip()
        if qid and qid not in target_ids:
            target_ids.append(qid)
        if len(target_ids) >= QUESTIONER_RETRY_TARGET_LIMIT:
            break
    return target_ids


async def increment_retry_for_questioner_node(state: AgentState) -> dict[str, Any]:
    target_ids = _retry_target_question_ids(state)
    return {
        "retry_count": state.get("retry_count", 0) + 1,
        "questioner_retry_count": state.get("questioner_retry_count", 0) + 1,
        "human_action": "regenerate_question" if target_ids else None,
        "target_question_ids": target_ids,
        "additional_instruction": "낮은 점수 질문만 재생성하고 통과한 질문과 중복되지 않게 보완하세요.",
        "retry_feedback": _retry_feedback(state),
    }


async def increment_retry_for_driller_node(state: AgentState) -> dict[str, Any]:
    return {
        "retry_count": state.get("retry_count", 0) + 1,
        "driller_retry_count": state.get("driller_retry_count", 0) + 1,
        "follow_ups": [],
        "retry_feedback": _retry_feedback(state),
    }


async def selector_node(state: AgentState) -> dict[str, Any]:
    reviews_by_id = {str(item.get("question_id")): item for item in state.get("reviews", [])}
    scores_by_id = {str(item.get("question_id")): item for item in state.get("scores", [])}
    return {
        "questions": _select_question_candidates(
            state.get("questions", []),
            reviews_by_id=reviews_by_id,
            scores_by_id=scores_by_id,
            limit=5,
        ),
    }


async def final_formatter_node(state: AgentState) -> dict[str, Any]:
    items: list[InterviewQuestionItem] = []
    answers = state.get("answers", [])
    follow_ups = state.get("follow_ups", [])
    reviews = state.get("reviews", [])
    scores = state.get("scores", [])

    for index, question in enumerate(state.get("questions", [])):
        question_id = _question_id(question, index)
        question["id"] = question_id
        question_model = QuestionCandidate.model_validate(question)
        answer = PredictedAnswer.model_validate(
            _find_by_question_id(answers, question_id) or _fallback_answer(question_id)
        )
        follow_up = FollowUpQuestion.model_validate(
            _find_by_question_id(follow_ups, question_id) or _fallback_follow_up(question_id)
        )
        review = ReviewResult.model_validate(
            _find_by_question_id(reviews, question_id) or _fallback_review(question_id)
        )
        score = ScoreResult.model_validate(
            _find_by_question_id(scores, question_id) or _fallback_score(question_id)
        )
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
        or {"job_fit": "문서 분석 결과가 없어 직무 적합성 판단이 제한됩니다."}
    )
    approved_count = sum(1 for item in items if item.review.status == "approved")
    is_partial = (
        len(items) < 5
        or approved_count < len(items)
        or state.get("retry_count", 0) >= state.get("max_retry_count", 2)
        or bool(state.get("node_warnings"))
    )
    response = QuestionGenerationResponse(
        session_id=state.get("session_id"),
        candidate_id=state.get("candidate_id"),
        target_job=state.get("target_job") or "",
        difficulty_level=state.get("difficulty_level"),
        status="partial_completed" if is_partial else "completed",
        analysis_summary=analysis,
        questions=items,
        generation_metadata={
            "pipeline": "jy",
            "graph": "build_state -> analyzer -> questioner -> selector_lite -> predictor -> driller -> reviewer -> scorer -> selector -> final_formatter",
            "driller_execution": "question_level_parallel_after_predictor",
            "total_candidate_questions": len(state.get("questions", [])),
            "selected_question_count": len(items),
            "retry_count": state.get("retry_count", 0),
            "questioner_retry_count": state.get("questioner_retry_count", 0),
            "driller_retry_count": state.get("driller_retry_count", 0),
            "router_decision": state.get("router_decision") or "selector",
            "is_all_approved": bool(items) and approved_count == len(items),
            "review_summary": state.get("review_summary", {}),
            "node_warnings": state.get("node_warnings", []),
        },
    )
    return {"final_response": response.model_dump(mode="json")}
