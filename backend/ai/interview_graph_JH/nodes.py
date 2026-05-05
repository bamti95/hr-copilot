"""LangGraph nodes for JH interview question generation.

This version keeps the original graph concept but changes the reviewer into an
evaluator/ranker.  The reviewer no longer decides "pass or retry" for every
selected question.  It scores the candidate pool, then the selector chooses the
best five.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from statistics import mean
from typing import Any
from uuid import uuid4

from .llm_usage import StructuredOutputCallError, call_structured_output_with_usage
from .prompts import (
    DRILLER_SYSTEM_PROMPT,
    DRILLER_USER_PROMPT,
    PREDICTOR_SYSTEM_PROMPT,
    PREDICTOR_USER_PROMPT,
    QUESTIONER_SYSTEM_PROMPT,
    QUESTIONER_USER_PROMPT,
    REVIEWER_SYSTEM_PROMPT,
    REVIEWER_USER_PROMPT,
)
from .schemas import (
    DrillerOutput,
    HARD_REVIEW_ISSUES,
    InterviewQuestionItem,
    PredictedAnswer,
    PredictorOutput,
    QuestionCandidate,
    QuestionGenerationResponse,
    QuestionQualityRubric,
    QuestionerOutput,
    ReviewResult,
    ReviewedQuestion,
    ReviewerOutput,
    EvaluationGuideRubric,
)
from .state import AgentState, QuestionSet


DEFAULT_REQUESTED_COUNT = 5
INITIAL_CANDIDATE_COUNT = 10
RETRY_CANDIDATE_COUNT = 5
MAX_RETRY_COUNT = 2
MIN_SELECTABLE_SCORE = 3.0
STRONG_SELECTABLE_SCORE = 3.6


def _safe_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _clip_text(text: str | None, limit: int) -> str:
    if not text:
        return ""
    normalized = re.sub(r"\s+", " ", str(text)).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "..."


def _list_from_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _average(values: dict[str, int] | None, fallback: float = 3.0) -> float:
    if not values:
        return fallback
    nums = [float(v) for v in values.values() if isinstance(v, int | float)]
    return round(mean(nums), 2) if nums else fallback


def _next_question_id(questions: list[QuestionSet]) -> str:
    existing = {str(question.get("id", "")) for question in questions}
    while True:
        candidate = f"jh-{uuid4().hex[:10]}"
        if candidate not in existing:
            return candidate


def _requested_count(state: AgentState) -> int:
    requested = state.get("requested_count") or DEFAULT_REQUESTED_COUNT
    try:
        requested = int(requested)
    except (TypeError, ValueError):
        requested = DEFAULT_REQUESTED_COUNT
    return max(1, requested)


def _candidate_context(state: AgentState) -> str:
    parts: list[str] = []
    for label, key in (
        ("이력서", "resume"),
        ("자기소개서", "cover_letter"),
        ("포트폴리오", "portfolio"),
    ):
        value = _clip_text(state.get(key), 7000)
        if value:
            parts.append(f"[{label}]\n{value}")
    return "\n\n".join(parts).strip()


def _existing_questions_for_prompt(state: AgentState) -> str:
    questions = state.get("questions") or []
    external = state.get("existing_questions") or []
    compact: list[dict[str, Any]] = []

    for question in questions:
        compact.append(
            {
                "id": question.get("id"),
                "status": question.get("status"),
                "question_text": question.get("question_text"),
                "score": question.get("score"),
                "review_reason": question.get("review_reason"),
            }
        )
    for item in external:
        text = item.get("question") or item.get("question_text")
        if text:
            compact.append(
                {
                    "id": item.get("id"),
                    "status": item.get("status") or item.get("review_status"),
                    "question_text": text,
                }
            )
    return _safe_json(compact[:30])


def _format_questions_for_llm(questions: list[QuestionSet]) -> str:
    payload: list[dict[str, Any]] = []
    for question in questions:
        payload.append(
            {
                "id": question.get("id"),
                "category": question.get("category"),
                "generation_basis": question.get("generation_basis"),
                "document_evidence": question.get("document_evidence"),
                "question_text": question.get("question_text"),
                "evaluation_guide": question.get("evaluation_guide"),
                "predicted_answer": question.get("predicted_answer"),
                "predicted_answer_basis": question.get("predicted_answer_basis"),
                "follow_up_questions": question.get("follow_up_questions", []),
            }
        )
    return _safe_json(payload)


def _review_guidance(questions: list[QuestionSet]) -> str:
    weak_items: list[dict[str, Any]] = []
    for question in questions:
        status = question.get("review_status") or question.get("status")
        if status not in {"needs_revision", "rejected"}:
            continue
        weak_items.append(
            {
                "question_text": question.get("question_text"),
                "status": status,
                "reason": question.get("review_reason") or question.get("reject_reason"),
                "recommended_revision": question.get("recommended_revision"),
                "issue_types": question.get("review_issue_types", []),
            }
        )
    return _safe_json(weak_items[:10]) if weak_items else "없음"


def _task_instruction(state: AgentState, generation_mode: str) -> str:
    requested = _requested_count(state)
    if generation_mode == "initial":
        return (
            f"질문 후보 {INITIAL_CANDIDATE_COUNT}개를 생성하세요. "
            f"최종 선택 목표는 {requested}개이므로 카테고리와 검증 역량이 겹치지 않게 만드세요."
        )
    if generation_mode == "retry_candidates":
        return (
            f"평가 결과 상위 {requested}개를 안정적으로 뽑기 위해 보완 후보 "
            f"{RETRY_CANDIDATE_COUNT}개를 추가 생성하세요. 기존 좋은 후보를 반복하지 말고, "
            "평가 피드백의 약점을 피한 새 후보를 만드세요."
        )
    if generation_mode == "add_question":
        return f"사용자 요청에 맞춰 새 질문 후보 {requested}개를 추가 생성하세요."
    return (
        "선택된 기존 질문을 사용자 피드백에 맞춰 다시 작성하세요. "
        "질문 의도는 유지하되 문서 근거와 평가가이드를 더 선명하게 만드세요."
    )


def _generation_mode(state: AgentState) -> str:
    action = state.get("human_action") or "generate"
    if action == "add_question":
        return "add_question"
    if action in {"regenerate_selected", "regenerate_batch"}:
        return "rewrite_selected"

    questions = state.get("questions") or []
    retry_count = int(state.get("retry_count") or 0)
    if questions and retry_count < int(state.get("max_retry_count") or MAX_RETRY_COUNT):
        selected = select_top_questions(questions, _requested_count(state))
        selectable_count = len([q for q in questions if _is_selectable(q)])
        if len(selected) < _requested_count(state) or selectable_count < _requested_count(state):
            return "retry_candidates"
    return "initial" if not questions else "retry_candidates"


def _target_ids(state: AgentState) -> set[str]:
    return {str(value) for value in state.get("selected_question_ids", [])}


def _candidate_to_question(candidate: QuestionCandidate, question_id: str) -> QuestionSet:
    return {
        "id": question_id,
        "category": candidate.category.strip() or "직무역량",
        "generation_basis": candidate.generation_basis.strip(),
        "document_evidence": candidate.document_evidence.strip(),
        "question_text": candidate.question_text.strip(),
        "evaluation_guide": candidate.evaluation_guide.strip(),
        "status": "pending",
        "review_status": "pending",
        "review_issue_types": [],
        "requested_revision_fields": [],
        "score": 0.0,
        "score_reason": "",
        "is_selectable": False,
        "selection_reason": "",
        "review_strengths": [],
        "review_risks": [],
        "follow_up_questions": [],
        "follow_up_intents": [],
    }


def _apply_candidates(
    existing: list[QuestionSet],
    candidates: list[QuestionCandidate],
    mode: str,
    state: AgentState,
) -> list[QuestionSet]:
    questions = deepcopy(existing)
    targets = _target_ids(state)

    if mode == "rewrite_selected" and targets:
        replacement_iter = iter(candidates)
        rewritten: list[QuestionSet] = []
        for question in questions:
            if str(question.get("id")) not in targets and str(
                question.get("original_question_id")
            ) not in targets:
                rewritten.append(question)
                continue
            try:
                candidate = next(replacement_iter)
            except StopIteration:
                rewritten.append(question)
                continue
            merged = _candidate_to_question(candidate, str(question.get("id")))
            merged["original_question_id"] = question.get("original_question_id")
            merged["generation_mode"] = mode
            rewritten.append(merged)
        for candidate in replacement_iter:
            new_question = _candidate_to_question(candidate, _next_question_id(rewritten))
            new_question["generation_mode"] = mode
            rewritten.append(new_question)
        return rewritten

    for candidate in candidates:
        new_question = _candidate_to_question(candidate, _next_question_id(questions))
        new_question["generation_mode"] = mode
        questions.append(new_question)
    return questions


def _question_text_key(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


def _questions_to_evaluate(questions: list[QuestionSet]) -> list[QuestionSet]:
    targets: list[QuestionSet] = []
    for question in questions:
        if question.get("status") in {"pending", "human_rejected"}:
            targets.append(question)
    return targets


def _hard_issue(issue_types: list[str]) -> bool:
    return bool(set(issue_types) & HARD_REVIEW_ISSUES)


def _normalize_status(review: ReviewResult) -> str:
    issue_types = _list_from_value(review.issue_types)
    score = float(review.overall_score or 0)

    if _hard_issue(issue_types):
        return "rejected" if score < 3.2 else "needs_revision"
    if review.status == "rejected" and score >= STRONG_SELECTABLE_SCORE:
        return "needs_revision"
    if score >= STRONG_SELECTABLE_SCORE and review.is_selectable:
        return "approved"
    if score >= MIN_SELECTABLE_SCORE and review.status != "rejected":
        return "needs_revision"
    return "rejected"


def _review_to_question(question: QuestionSet, review: ReviewResult) -> QuestionSet:
    status = _normalize_status(review)
    issue_types = _list_from_value(review.issue_types)
    quality_scores = review.question_quality_scores.model_dump()
    guide_scores = review.evaluation_guide_scores.model_dump()
    score = round(float(review.overall_score or 0), 2)
    selectable = status != "rejected" and bool(review.is_selectable) and score >= MIN_SELECTABLE_SCORE

    updated = deepcopy(question)
    updated.update(
        {
            "status": status,
            "review_status": status,
            "review_reason": review.reason.strip(),
            "recommended_revision": review.recommended_revision.strip(),
            "reject_reason": review.reject_reason.strip() if status == "rejected" else "",
            "review_issue_types": issue_types,
            "requested_revision_fields": _list_from_value(review.requested_revision_fields),
            "question_quality_scores": quality_scores,
            "evaluation_guide_scores": guide_scores,
            "question_quality_average": _average(quality_scores),
            "evaluation_guide_average": _average(guide_scores),
            "score": score,
            "score_reason": review.reason.strip(),
            "is_selectable": selectable,
            "selection_reason": review.selection_reason.strip() or review.reason.strip(),
            "review_strengths": _list_from_value(review.strengths),
            "review_risks": _list_from_value(review.risks),
        }
    )
    return updated


def _fallback_review(question: QuestionSet, reason: str) -> ReviewResult:
    return ReviewResult(
        status="needs_revision",
        reason=reason,
        recommended_revision="질문과 평가가이드가 문서 근거와 직무 역량을 더 명확히 연결하도록 보완하세요.",
        issue_types=["reviewer_fallback"],
        requested_revision_fields=["question_text", "evaluation_guide"],
        question_quality_scores=QuestionQualityRubric(
            job_relevance=3,
            document_grounding=3,
            competency_signal=3,
            specificity=3,
            clarity=3,
        ),
        evaluation_guide_scores=EvaluationGuideRubric(
            scoring_clarity=3,
            evidence_alignment=3,
            answer_discriminability=3,
            risk_awareness=3,
            interviewer_usability=3,
        ),
        overall_score=3.0,
        selection_reason="리뷰어 응답 매칭 실패로 보수적으로 평가했습니다.",
        strengths=[],
        risks=["reviewer_fallback"],
        is_selectable=True,
    )


def _is_selectable(question: QuestionSet) -> bool:
    if question.get("status") == "rejected" or question.get("review_status") == "rejected":
        return False
    if question.get("is_selectable") is False:
        return False
    return float(question.get("score") or 0) >= MIN_SELECTABLE_SCORE


def _selection_key(question: QuestionSet) -> tuple[float, float, float, int, int]:
    status_bonus = 0.35 if question.get("review_status") == "approved" else 0.0
    evidence_bonus = 0.15 if question.get("document_evidence") else 0.0
    score = float(question.get("score") or 0)
    quality = float(question.get("question_quality_average") or 0)
    guide = float(question.get("evaluation_guide_average") or 0)
    risk_penalty = len(question.get("review_risks", []) or [])
    issue_penalty = len(question.get("review_issue_types", []) or [])
    return (
        score + status_bonus + evidence_bonus,
        quality,
        guide,
        -risk_penalty,
        -issue_penalty,
    )


def select_top_questions(questions: list[QuestionSet], requested_count: int) -> list[QuestionSet]:
    eligible = [question for question in questions if _is_selectable(question)]
    ranked = sorted(eligible, key=_selection_key, reverse=True)

    selected: list[QuestionSet] = []
    seen_categories: set[str] = set()

    for question in ranked:
        category = str(question.get("category") or "")
        if category in seen_categories and len(ranked) >= requested_count + 2:
            continue
        selected.append(question)
        seen_categories.add(category)
        if len(selected) >= requested_count:
            break

    if len(selected) < requested_count:
        selected_ids = {question.get("id") for question in selected}
        for question in ranked:
            if question.get("id") in selected_ids:
                continue
            selected.append(question)
            if len(selected) >= requested_count:
                break

    finalized: list[QuestionSet] = []
    for index, question in enumerate(selected[:requested_count], start=1):
        updated = deepcopy(question)
        updated["selection_rank"] = index
        finalized.append(updated)
    return finalized


def _response_selection(state: AgentState, requested_count: int) -> list[QuestionSet]:
    target_ids = _target_ids(state)
    action = state.get("human_action")
    questions = state.get("questions") or []
    if action in {"regenerate_selected", "regenerate_batch"} and target_ids:
        targets = [
            question
            for question in questions
            if str(question.get("id")) in target_ids
            or str(question.get("original_question_id")) in target_ids
        ]
        selected_targets = select_top_questions(targets, max(1, len(target_ids)))
        if selected_targets:
            return selected_targets
    return state.get("selected_questions") or select_top_questions(questions, requested_count)


def _merge_question_lists(
    current: list[QuestionSet],
    reviewed_updates: dict[str, QuestionSet],
) -> list[QuestionSet]:
    merged: list[QuestionSet] = []
    for question in current:
        key = str(question.get("id"))
        merged.append(reviewed_updates.get(key, question))
    return merged


def prepare_context_node(state: AgentState) -> AgentState:
    candidate_context = _candidate_context(state)
    context = "\n\n".join(
        part
        for part in (
            f"[채용공고]\n{_clip_text(state.get('job_posting'), 7000)}",
            f"[지원자 문서]\n{candidate_context}",
        )
        if part.strip()
    )
    return {
        **state,
        "context": context,
        "candidate_context": candidate_context,
        "questions": deepcopy(state.get("questions") or []),
        "retry_count": int(state.get("retry_count") or 0),
        "max_retry_count": int(state.get("max_retry_count") or MAX_RETRY_COUNT),
        "errors": list(state.get("errors") or []),
        "raw_outputs": dict(state.get("raw_outputs") or {}),
    }


async def questioner_node(state: AgentState) -> AgentState:
    errors = list(state.get("errors") or [])
    raw_outputs = dict(state.get("raw_outputs") or {})
    mode = _generation_mode(state)
    questions = deepcopy(state.get("questions") or [])

    prompt = QUESTIONER_USER_PROMPT.format(
        job_posting=state.get("job_posting") or "",
        candidate_context=state.get("candidate_context") or _candidate_context(state),
        company_name=state.get("company_name") or "",
        applicant_name=state.get("applicant_name") or "",
        existing_questions=_existing_questions_for_prompt(state),
        generation_mode=mode,
        requested_count=(
            INITIAL_CANDIDATE_COUNT
            if mode == "initial"
            else RETRY_CANDIDATE_COUNT
            if mode == "retry_candidates"
            else _requested_count(state)
        ),
        feedback=state.get("feedback") or "",
        regen_targets=_safe_json(list(_target_ids(state))),
        retry_guidance=_review_guidance(questions),
        task_instruction=_task_instruction(state, mode),
    )

    try:
        output, usages = await call_structured_output_with_usage(
            node_name="questioner",
            system_prompt=QUESTIONER_SYSTEM_PROMPT,
            user_prompt=prompt,
            response_model=QuestionerOutput,
        )
    except StructuredOutputCallError as exc:
        errors.append(f"questioner 호출 실패: {exc}")
        return {
            **state,
            "errors": errors,
            "raw_outputs": raw_outputs,
            "llm_usages": list(state.get("llm_usages") or []) + exc.usages,
            "status": "failed",
        }
    except Exception as exc:  # noqa: BLE001
        errors.append(f"questioner 호출 실패: {exc}")
        return {**state, "errors": errors, "raw_outputs": raw_outputs, "status": "failed"}

    raw_outputs["questioner"] = {
        "mode": mode,
        "output": output.model_dump(mode="json"),
    }

    next_questions = _apply_candidates(questions, output.questions, mode, state)
    retry_count = int(state.get("retry_count") or 0)
    if mode == "retry_candidates":
        retry_count += 1

    return {
        **state,
        "questions": next_questions,
        "retry_count": retry_count,
        "errors": errors,
        "raw_outputs": raw_outputs,
        "llm_usages": list(state.get("llm_usages") or []) + usages,
        "status": "pending",
    }


async def predictor_node(state: AgentState) -> AgentState:
    errors = list(state.get("errors") or [])
    raw_outputs = dict(state.get("raw_outputs") or {})
    questions = deepcopy(state.get("questions") or [])
    targets = [question for question in questions if not question.get("predicted_answer")]
    if not targets:
        return state

    prompt = PREDICTOR_USER_PROMPT.format(
        candidate_context=state.get("candidate_context") or _candidate_context(state),
        questions=_format_questions_for_llm(targets),
    )
    try:
        output, usages = await call_structured_output_with_usage(
            node_name="predictor",
            system_prompt=PREDICTOR_SYSTEM_PROMPT,
            user_prompt=prompt,
            response_model=PredictorOutput,
        )
    except StructuredOutputCallError as exc:
        errors.append(f"predictor 호출 실패: {exc}")
        return {
            **state,
            "errors": errors,
            "raw_outputs": raw_outputs,
            "llm_usages": list(state.get("llm_usages") or []) + exc.usages,
        }
    except Exception as exc:  # noqa: BLE001
        errors.append(f"predictor 호출 실패: {exc}")
        return {**state, "errors": errors, "raw_outputs": raw_outputs}

    raw_outputs["predictor"] = {"output": output.model_dump(mode="json")}

    by_text = {
        _question_text_key(answer.question_text): answer
        for answer in output.answers
        if isinstance(answer, PredictedAnswer)
    }
    for question in questions:
        answer = by_text.get(_question_text_key(question.get("question_text")))
        if not answer:
            continue
        question["predicted_answer"] = answer.predicted_answer.strip()
        question["predicted_answer_basis"] = answer.predicted_answer_basis.strip()

    return {
        **state,
        "questions": questions,
        "errors": errors,
        "raw_outputs": raw_outputs,
        "llm_usages": list(state.get("llm_usages") or []) + usages,
    }


async def driller_node(state: AgentState) -> AgentState:
    errors = list(state.get("errors") or [])
    raw_outputs = dict(state.get("raw_outputs") or {})
    questions = deepcopy(state.get("questions") or [])
    targets = [question for question in questions if not question.get("follow_up_questions")]
    if not targets:
        return state

    prompt = DRILLER_USER_PROMPT.format(
        job_posting=state.get("job_posting") or "",
        candidate_context=state.get("candidate_context") or _candidate_context(state),
        questions=_format_questions_for_llm(targets),
    )
    try:
        output, usages = await call_structured_output_with_usage(
            node_name="driller",
            system_prompt=DRILLER_SYSTEM_PROMPT,
            user_prompt=prompt,
            response_model=DrillerOutput,
        )
    except StructuredOutputCallError as exc:
        errors.append(f"driller 호출 실패: {exc}")
        return {
            **state,
            "errors": errors,
            "raw_outputs": raw_outputs,
            "llm_usages": list(state.get("llm_usages") or []) + exc.usages,
        }
    except Exception as exc:  # noqa: BLE001
        errors.append(f"driller 호출 실패: {exc}")
        return {**state, "errors": errors, "raw_outputs": raw_outputs}

    raw_outputs["driller"] = {"output": output.model_dump(mode="json")}

    by_text = {
        _question_text_key(item.question_text): item
        for item in output.follow_ups
        if item.question_text
    }
    for question in questions:
        item = by_text.get(_question_text_key(question.get("question_text")))
        if not item:
            continue
        question["follow_up_questions"] = [
            _clip_text(text, 300) for text in item.follow_up_questions
        ]
        question["follow_up_intents"] = [
            _clip_text(text, 300) for text in item.follow_up_intents
        ]

    return {
        **state,
        "questions": questions,
        "errors": errors,
        "raw_outputs": raw_outputs,
        "llm_usages": list(state.get("llm_usages") or []) + usages,
    }


async def reviewer_node(state: AgentState) -> AgentState:
    errors = list(state.get("errors") or [])
    raw_outputs = dict(state.get("raw_outputs") or {})
    questions = deepcopy(state.get("questions") or [])
    targets = _questions_to_evaluate(questions)
    requested = _requested_count(state)

    if not targets:
        selected = select_top_questions(questions, requested)
        return {
            **state,
            "selected_questions": selected,
            "is_all_approved": all(q.get("review_status") == "approved" for q in selected),
            "questions": questions,
            "errors": errors,
            "raw_outputs": raw_outputs,
        }

    prompt = REVIEWER_USER_PROMPT.format(
        job_posting=state.get("job_posting") or "",
        candidate_context=state.get("candidate_context") or _candidate_context(state),
        questions=_format_questions_for_llm(targets),
    )
    try:
        output, usages = await call_structured_output_with_usage(
            node_name="reviewer",
            system_prompt=REVIEWER_SYSTEM_PROMPT,
            user_prompt=prompt,
            response_model=ReviewerOutput,
        )
    except StructuredOutputCallError as exc:
        errors.append(f"reviewer 호출 실패: {exc}")
        output = ReviewerOutput(
            reviews=[
                ReviewedQuestion(
                    question_text=question.get("question_text") or "",
                    review=_fallback_review(question, "리뷰어 호출 실패"),
                )
                for question in targets
            ]
        )
        usages = exc.usages
    except Exception as exc:  # noqa: BLE001
        errors.append(f"reviewer 호출 실패: {exc}")
        output = ReviewerOutput(
            reviews=[
                ReviewedQuestion(
                    question_text=question.get("question_text") or "",
                    review=_fallback_review(question, "리뷰어 호출 실패"),
                )
                for question in targets
            ]
        )
        usages = []

    raw_outputs["reviewer"] = {"output": output.model_dump(mode="json")}
    reviews_by_text = {
        _question_text_key(item.question_text): item.review
        for item in output.reviews
        if isinstance(item, ReviewedQuestion)
    }

    updates: dict[str, QuestionSet] = {}
    for question in targets:
        review = reviews_by_text.get(_question_text_key(question.get("question_text")))
        if review is None:
            review = _fallback_review(question, "리뷰어가 해당 질문 평가를 반환하지 않았습니다.")
        updates[str(question.get("id"))] = _review_to_question(question, review)

    merged = _merge_question_lists(questions, updates)
    selected = select_top_questions(merged, requested)
    return {
        **state,
        "questions": merged,
        "selected_questions": selected,
        "is_all_approved": all(q.get("review_status") == "approved" for q in selected),
        "errors": errors,
        "raw_outputs": raw_outputs,
        "llm_usages": list(state.get("llm_usages") or []) + usages,
    }


def review_router(state: AgentState) -> str:
    if state.get("status") == "failed":
        return "end"

    requested = _requested_count(state)
    selected = state.get("selected_questions") or select_top_questions(
        state.get("questions") or [],
        requested,
    )
    retry_count = int(state.get("retry_count") or 0)
    max_retry = int(state.get("max_retry_count") or MAX_RETRY_COUNT)

    if len(selected) >= requested:
        average_score = mean(float(question.get("score") or 0) for question in selected)
        approved_count = len(
            [question for question in selected if question.get("review_status") == "approved"]
        )
        enough_quality = average_score >= STRONG_SELECTABLE_SCORE and approved_count >= min(
            3,
            requested,
        )
        if enough_quality or retry_count >= max_retry:
            return "end"
        return "retry"
    if retry_count < max_retry:
        return "retry"
    return "end"


def _review_model_from_question(question: QuestionSet) -> ReviewResult:
    status = question.get("review_status")
    if status not in {"approved", "needs_revision", "rejected"}:
        status = "needs_revision"

    return ReviewResult(
        question_id=str(question.get("id") or ""),
        status=status,
        reason=question.get("review_reason") or question.get("score_reason") or "",
        recommended_revision=question.get("recommended_revision") or "",
        reject_reason=question.get("reject_reason") or "",
        issue_types=_list_from_value(question.get("review_issue_types")),
        requested_revision_fields=_list_from_value(
            question.get("requested_revision_fields")
        ),
        question_quality_scores=QuestionQualityRubric.model_validate(
            question.get("question_quality_scores") or {}
        ),
        evaluation_guide_scores=EvaluationGuideRubric.model_validate(
            question.get("evaluation_guide_scores") or {}
        ),
        overall_score=max(1.0, min(5.0, float(question.get("score") or 3.0))),
        selection_reason=question.get("selection_reason") or "",
        strengths=_list_from_value(question.get("review_strengths")),
        risks=_list_from_value(question.get("review_risks")),
        is_selectable=bool(question.get("is_selectable", True)),
    )


def build_response(state: AgentState) -> QuestionGenerationResponse:
    requested = _requested_count(state)
    questions = state.get("questions") or []
    selected = _response_selection(state, requested)
    errors = list(state.get("errors") or [])
    retry_count = int(state.get("retry_count") or 0)
    enough_selected = len(selected) >= requested

    items: list[InterviewQuestionItem] = []
    for question in selected[:requested]:
        review = _review_model_from_question(question)
        items.append(
            InterviewQuestionItem(
                id=str(question.get("id") or ""),
                category=question.get("category") or "직무역량",
                question_text=question.get("question_text") or "",
                generation_basis=question.get("generation_basis") or review.selection_reason,
                document_evidence=_list_from_value(question.get("document_evidence")),
                evaluation_guide=question.get("evaluation_guide") or "",
                predicted_answer=question.get("predicted_answer") or "",
                predicted_answer_basis=question.get("predicted_answer_basis") or "",
                follow_up_question=(
                    _list_from_value(question.get("follow_up_questions")) or [""]
                )[0],
                follow_up_basis=(
                    _list_from_value(question.get("follow_up_intents")) or [""]
                )[0],
                follow_up_questions=_list_from_value(question.get("follow_up_questions")),
                follow_up_intents=_list_from_value(question.get("follow_up_intents")),
                risk_tags=_list_from_value(question.get("review_risks")),
                competency_tags=[question.get("category") or "직무역량"],
                review=review,
                score=int(round(float(question.get("score") or 0) * 20)),
                score_reason=question.get("score_reason") or question.get("review_reason") or "",
            )
        )

    if state.get("status") == "failed" or (errors and not items):
        status = "failed"
    elif enough_selected:
        status = "completed"
    else:
        status = "partial_completed"

    return QuestionGenerationResponse(
        session_id=int(state.get("session_id") or 0),
        candidate_id=int(state.get("candidate_id") or 0),
        target_job=str(state.get("target_job") or ""),
        difficulty_level=state.get("difficulty_level"),
        status=status,
        questions=items,
        analysis_summary={
            "job_fit": "지원자 문서와 채용공고를 근거로 면접 질문 후보를 평가하고 상위 질문을 선별했습니다.",
            "risks": errors,
        },
        generation_metadata={
            "candidate_count": len(questions),
            "selected_count": len(items),
            "retry_count": retry_count,
            "approved_selected_count": len(
                [item for item in items if item.review.status == "approved"]
            ),
            "all_selected_approved": all(
                item.review.status == "approved" for item in items
            )
            if items
            else False,
            "selection_policy": "reviewer_scores_all_candidates_selector_returns_top_n",
        },
    )
