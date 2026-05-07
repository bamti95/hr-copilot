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
from difflib import SequenceMatcher
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
    VERIFICATION_EXTRACTOR_SYSTEM_PROMPT,
    VERIFICATION_EXTRACTOR_USER_PROMPT,
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
    VerificationProfileOutput,
)
from .state import AgentState, QuestionSet


DEFAULT_REQUESTED_COUNT = 5
INITIAL_CANDIDATE_COUNT = 14
RETRY_CANDIDATE_COUNT = 7
MAX_RETRY_COUNT = 2
MIN_SELECTABLE_SCORE = 3.0
STRONG_SELECTABLE_SCORE = 3.6
QUESTION_TEXT_LIMIT = 140
PREDICTED_ANSWER_LIMIT = 260
PREDICTED_BASIS_LIMIT = 180
PEOPLE_FOCUS_AREAS = {"collaboration", "culture_fit"}


def _safe_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _clip_text(text: str | None, limit: int) -> str:
    if not text:
        return ""
    normalized = re.sub(r"\s+", " ", str(text)).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "..."


def _compact_sentences(text: str | None, *, max_sentences: int, limit: int) -> str:
    normalized = _clip_text(text, limit * 2)
    if not normalized:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", normalized)
    compact = " ".join(part.strip() for part in parts[:max_sentences] if part.strip())
    return _clip_text(compact or normalized, limit)


def _normalize_question_text(text: str | None) -> str:
    normalized = _clip_text(text, QUESTION_TEXT_LIMIT)
    normalized = normalized.strip(" \"'")
    if normalized.count("?") > 1:
        normalized = normalized.split("?", 1)[0].strip() + "?"
    return _clip_text(normalized, QUESTION_TEXT_LIMIT)


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


def _prompt_profile_summary(state: AgentState) -> str:
    profile_key = state.get("prompt_profile_key") or ""
    profile_target_job = state.get("prompt_profile_target_job") or ""
    system_prompt = _clip_text(state.get("prompt_profile_system_prompt"), 2500)
    output_schema = _clip_text(_safe_json(state.get("prompt_profile_output_schema")), 1200)

    summary = {
        "profile_key": profile_key,
        "target_job": profile_target_job,
        "system_prompt": system_prompt,
        "output_schema": output_schema,
    }
    return _safe_json(summary)


def _verification_profile_for_prompt(state: AgentState) -> str:
    profile = state.get("verification_profile") or {}
    return _safe_json(profile) if profile else "{}"


def _context_snippet(text: str, keyword: str, *, window: int = 170) -> str:
    index = text.find(keyword)
    if index < 0:
        return ""
    start = max(0, index - 35)
    end = min(len(text), index + window)
    return _clip_text(text[start:end], 220)


def _first_matching_snippet(text: str, keywords: tuple[str, ...]) -> str:
    for keyword in keywords:
        snippet = _context_snippet(text, keyword)
        if snippet:
            return snippet
    return ""


def _candidate_text_for_heuristics(state: AgentState) -> str:
    return str(state.get("candidate_context") or _candidate_context(state) or "")


def _heuristic_verification_profile(state: AgentState) -> dict[str, Any]:
    """Seed obvious verification points so the extractor never starts from zero.

    These heuristics are intentionally conservative. They do not replace the
    LLM judgement; they highlight document patterns that real interviewers
    almost always want to verify.
    """

    text = _candidate_text_for_heuristics(state)
    seed: dict[str, Any] = {
        "must_verify_points": [],
        "strength_points": [],
        "ambiguity_points": [],
        "recommended_question_mix": {
            "technical_depth": 2,
            "performance_ownership": 1,
            "career_context": 1,
            "collaboration_or_culture_fit": 1,
            "growth_adaptability": 1,
        },
    }

    def add_point(
        bucket: str,
        *,
        dimension: str,
        signal_type: str,
        severity: str,
        evidence: str,
        why_it_matters: str,
        question_angle: str,
        avoid: str,
        must_ask: bool,
    ) -> None:
        if not evidence:
            return
        existing = seed[bucket]
        if any(
            item["dimension"] == dimension
            and item["signal_type"] == signal_type
            and item["evidence"] == evidence
            for item in existing
        ):
            return
        existing.append(
            {
                "dimension": dimension,
                "signal_type": signal_type,
                "severity": severity,
                "evidence": evidence,
                "why_it_matters": why_it_matters,
                "question_angle": question_angle,
                "avoid": avoid,
                "must_ask": must_ask,
            }
        )

    if any(keyword in text for keyword in ("임금체불", "공백", "퇴사 이후", "복귀", "재취업")):
        add_point(
            "must_verify_points",
            dimension="career_context",
            signal_type="return_to_work_readiness",
            severity="high",
            evidence=_first_matching_snippet(
                text, ("임금체불", "공백", "퇴사 이후", "복귀", "재취업")
            ),
            why_it_matters=(
                "공백 사유 자체보다 복귀 준비도와 현재 업무 안정성을 확인해야 "
                "실무 적응 가능성을 판단할 수 있습니다."
            ),
            question_angle=(
                "민감한 개인 사정이 아니라 복귀를 위해 만든 산출물, 학습 기준, "
                "실무 감각 유지 방식으로 검증"
            ),
            avoid="치료 내용, 사생활, 개인적 트라우마를 직접 묻는 질문",
            must_ask=True,
        )

    explicit_transition_keywords = (
        "직무 전환",
        "커리어 전환",
        "진로 탐색",
        "영업으로 전환",
        "마케팅으로 전환",
        "개발자로 전환",
        "데이터 직무로 전환",
    )
    if any(keyword in text for keyword in explicit_transition_keywords):
        add_point(
            "must_verify_points",
            dimension="career_context",
            signal_type="career_transition_evidence",
            severity="high",
            evidence=_first_matching_snippet(
                text, explicit_transition_keywords
            ),
            why_it_matters=(
                "직무 전환은 관심 표현보다 실제 준비 행동과 직무 적합성 근거가 "
                "있는지 확인해야 합니다."
            ),
            question_angle=(
                "전환 동기 설명보다 실행 근거, 보완한 약점, 실전 경험으로 검증"
            ),
            avoid="막연한 흥미나 포부만 반복하게 하는 질문",
            must_ask=True,
        )

    metric_match = re.search(
        r"(\d+\s*(억|만|천만|%|배|건|곳|명))",
        text,
    )
    if metric_match and any(
        keyword in text for keyword in ("매출", "수주", "유치", "개선", "감소", "증가", "단축")
    ):
        add_point(
            "must_verify_points",
            dimension="performance_ownership",
            signal_type="metric_ownership",
            severity="high",
            evidence=_context_snippet(text, metric_match.group(1)),
            why_it_matters=(
                "큰 성과 수치는 매력적이지만, 본인 직접 기여와 측정 기준을 "
                "구분해서 확인해야 과장 위험을 줄일 수 있습니다."
            ),
            question_angle=(
                "대표 성과 1건을 골라 본인 액션, 팀 기여, 측정 기준을 분리해서 설명하게 함"
            ),
            avoid="성과 수치를 사실로 단정하거나 전부 본인 공로로 전제하는 질문",
            must_ask=True,
        )

    if any(keyword in text for keyword in ("부트캠프", "Kaggle", "온라인 강의", "학습", "프로젝트")):
        add_point(
            "ambiguity_points",
            dimension="growth_adaptability",
            signal_type="learning_to_execution",
            severity="medium",
            evidence=_first_matching_snippet(
                text, ("부트캠프", "Kaggle", "온라인 강의", "학습", "프로젝트")
            ),
            why_it_matters=(
                "학습 경험이 실제 운영 제약, 재현성, 협업 맥락으로 이어지는지 "
                "확인해야 실무 적응력을 판단할 수 있습니다."
            ),
            question_angle=(
                "학습 내용 소개보다 실전 적용, 실패 수정, 운영 제약 대응 경험으로 검증"
            ),
            avoid="수강 여부나 수료 사실만 확인하는 질문",
            must_ask=False,
        )

    if any(keyword in text for keyword in ("협업", "팀", "조율", "갈등", "피드백", "소통")):
        add_point(
            "ambiguity_points",
            dimension="collaboration",
            signal_type="collaboration_depth",
            severity="medium",
            evidence=_first_matching_snippet(
                text, ("협업", "팀", "조율", "갈등", "피드백", "소통")
            ),
            why_it_matters=(
                "최종 질문 5개 중 1개 정도는 실제 협업 방식과 피드백 수용성을 "
                "확인해야 조직 적응 가능성을 볼 수 있습니다."
            ),
            question_angle=(
                "갈등 유무가 아니라 의견 충돌 시 조정 기준과 행동 변화로 검증"
            ),
            avoid="성격 평가처럼 느껴지는 추상적 인성 질문",
            must_ask=False,
        )

    artifact_keywords = (
        "포트폴리오",
        "프로젝트",
        "깃허브",
        "github",
        "배포",
        "커밋",
        "산출물",
        "데모",
        "kaggle",
    )
    if any(keyword in text for keyword in ("공백", "복귀", "퇴사 이후", "재취업")) and not any(
        keyword in text.lower() for keyword in artifact_keywords
    ):
        add_point(
            "ambiguity_points",
            dimension="career_context",
            signal_type="gap_without_artifact",
            severity="high",
            evidence=_first_matching_snippet(text, ("공백", "복귀", "퇴사 이후", "재취업")),
            why_it_matters=(
                "공백기 이후의 준비를 증명할 산출물이 약하면, 시간을 어떻게 보냈는지와 "
                "왜 산출물 없이도 준비가 되었다고 볼 수 있는지까지 같이 확인해야 합니다."
            ),
            question_angle=(
                "산출물이 있으면 그것으로 검증하고, 없으면 공백기 동안의 루틴, 학습 방식, "
                "실무 감각 유지 방법, 복귀 준비 판단 기준을 함께 묻는 질문으로 설계"
            ),
            avoid="산출물이 없다는 이유만으로 무의미한 시간을 보냈다고 단정하는 질문",
            must_ask=True,
        )

    transition_keywords = explicit_transition_keywords
    reason_keywords = ("이유", "계기", "관심", "동기", "희망", "느꼈", "판단")
    if any(keyword in text for keyword in transition_keywords):
        signal_type = (
            "transition_reason_present"
            if any(keyword in text for keyword in reason_keywords)
            else "transition_reason_missing"
        )
        question_angle = (
            "문서에 적힌 전환 이유가 실제 행동과 준비로 이어졌는지, 약점을 어떻게 보완했는지 확인"
            if signal_type == "transition_reason_present"
            else "왜 전환하려는지, 무엇을 준비했는지, 그 준비를 어떤 증거로 보여줄 수 있는지 함께 확인"
        )
        add_point(
            "must_verify_points",
            dimension="career_context",
            signal_type=signal_type,
            severity="high",
            evidence=_first_matching_snippet(text, transition_keywords),
            why_it_matters=(
                "직무 전환은 이유의 설득력만이 아니라 실행 근거와 준비 수준이 함께 확인되어야 "
                "실제 전환 가능성을 판단할 수 있습니다."
            ),
            question_angle=question_angle,
            avoid="막연한 포부만 말하게 두거나 이유만 확인하고 끝내는 질문",
            must_ask=True,
        )

    learning_keywords = ("부트캠프", "kaggle", "강의", "자율학습", "온라인", "스터디")
    experience_keywords = ("인턴", "실무", "운영", "배포", "근무", "회사", "고객사")
    if any(keyword in text.lower() for keyword in learning_keywords) and not any(
        keyword in text for keyword in experience_keywords
    ):
        add_point(
            "must_verify_points",
            dimension="growth_adaptability",
            signal_type="learning_without_strong_artifact",
            severity="high",
            evidence=_first_matching_snippet(
                text, ("부트캠프", "Kaggle", "강의", "자율학습", "온라인", "스터디")
            ),
            why_it_matters=(
                "학습 이력이 많은 후보자는 '배웠다'와 '실제로 쓸 수 있다' 사이의 간극을 "
                "검증해야 합니다. 특히 포트폴리오나 산출물이 약하면 검증 질문이 더 구체적이어야 합니다."
            ),
            question_angle=(
                "포트폴리오/프로젝트가 있으면 그 근거를 직접 찌르고, 없으면 무엇을 만들거나 검증했는지, "
                "없는데도 실무 가능하다고 보는 이유가 무엇인지 함께 묻는 질문으로 설계"
            ),
            avoid="단순 수강 여부, 공부량 자랑만 확인하는 질문",
            must_ask=True,
        )

    return seed


def _merge_verification_profiles(
    llm_profile: dict[str, Any], heuristic_profile: dict[str, Any]
) -> dict[str, Any]:
    merged = deepcopy(llm_profile) if llm_profile else {}

    for bucket in ("must_verify_points", "strength_points", "ambiguity_points"):
        combined: list[dict[str, Any]] = list(merged.get(bucket) or [])
        seen = {
            (
                item.get("dimension"),
                item.get("signal_type"),
                item.get("evidence"),
            )
            for item in combined
        }
        for item in heuristic_profile.get(bucket, []):
            key = (item.get("dimension"), item.get("signal_type"), item.get("evidence"))
            if key in seen:
                continue
            combined.append(item)
            seen.add(key)
        merged[bucket] = combined

    if not merged.get("recommended_question_mix"):
        merged["recommended_question_mix"] = heuristic_profile.get("recommended_question_mix", {})

    return merged


def _target_question_feedback(state: AgentState) -> str:
    target_ids = _target_ids(state)
    if not target_ids:
        return "없음"

    feedback_items: list[dict[str, Any]] = []
    for question in state.get("questions") or []:
        if (
            str(question.get("id")) not in target_ids
            and str(question.get("original_question_id")) not in target_ids
        ):
            continue
        feedback_items.append(
            {
                "id": question.get("id"),
                "question_text": question.get("question_text"),
                "previous_review_status": question.get("previous_review_status")
                or question.get("review_status"),
                "previous_score": question.get("previous_score") or question.get("score"),
                "previous_review_reason": question.get("previous_review_reason")
                or question.get("review_reason"),
                "previous_score_reason": question.get("previous_score_reason")
                or question.get("score_reason"),
                "previous_recommended_revision": question.get("previous_recommended_revision")
                or question.get("recommended_revision"),
                "rewrite_feedback": question.get("rewrite_feedback") or "",
            }
        )
    return _safe_json(feedback_items) if feedback_items else "없음"


def _format_questions_for_llm(questions: list[QuestionSet]) -> str:
    payload: list[dict[str, Any]] = []
    for question in questions:
        payload.append(
            {
                "id": question.get("id"),
                "focus_area": question.get("focus_area"),
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


def _quality_gate(selected: list[QuestionSet], requested_count: int) -> tuple[bool, float, int]:
    if len(selected) < requested_count:
        return False, 0.0, 0
    average_score = round(mean(float(question.get("score") or 0) for question in selected), 2)
    approved_count = len(
        [question for question in selected if question.get("review_status") == "approved"]
    )
    enough_quality = average_score >= STRONG_SELECTABLE_SCORE and approved_count >= min(
        3,
        requested_count,
    )
    return enough_quality, average_score, approved_count


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
        selected = select_top_questions(
            questions,
            _requested_count(state),
            state.get("verification_profile"),
        )
        selectable_count = len([q for q in questions if _is_selectable(q)])
        if len(selected) < _requested_count(state) or selectable_count < _requested_count(state):
            return "retry_candidates"
    return "initial" if not questions else "retry_candidates"


def _target_ids(state: AgentState) -> set[str]:
    return {str(value) for value in state.get("selected_question_ids", [])}


def _candidate_to_question(candidate: QuestionCandidate, question_id: str) -> QuestionSet:
    return {
        "id": question_id,
        "focus_area": candidate.focus_area.strip() or "technical_depth",
        "category": candidate.category.strip() or "직무역량",
        "generation_basis": candidate.generation_basis.strip(),
        "document_evidence": candidate.document_evidence.strip(),
        "question_text": _normalize_question_text(candidate.question_text),
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
        "previous_review_status": "",
        "previous_review_reason": "",
        "previous_score_reason": "",
        "previous_recommended_revision": "",
        "previous_score": 0.0,
        "rewrite_feedback": "",
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
            merged["previous_review_status"] = question.get("previous_review_status") or question.get(
                "review_status"
            )
            merged["previous_review_reason"] = question.get("previous_review_reason") or question.get(
                "review_reason"
            )
            merged["previous_score_reason"] = question.get("previous_score_reason") or question.get(
                "score_reason"
            )
            merged["previous_recommended_revision"] = question.get(
                "previous_recommended_revision"
            ) or question.get("recommended_revision")
            merged["previous_score"] = float(
                question.get("previous_score") or question.get("score") or 0.0
            )
            merged["rewrite_feedback"] = question.get("rewrite_feedback") or ""
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


def _is_multi_track_question_text(text: str | None) -> bool:
    normalized = _question_text_key(text)
    if normalized.count("?") > 1:
        return True
    # Allow one question to walk through a single verification flow such as
    # "판단 -> 행동 변화 -> 결과". Flag only clear alternatives or unrelated splits.
    compound_markers = [" 혹은 ", " 또는 ", " / "]
    return any(marker in f" {normalized} " for marker in compound_markers)


def _focus_area_key(question: QuestionSet) -> str:
    return str(question.get("focus_area") or "").strip().lower()


def _normalize_overlap_source(text: str | None) -> str:
    source = (text or "").lower()
    return re.sub(r"\s+", " ", source)


def _metric_tokens_from_text(text: str | None) -> set[str]:
    source = _normalize_overlap_source(text)
    metric_pattern = re.compile(
        r"\d+(?:\.\d+)?\s*(?:%|퍼센트|건|회|배|명|시간|일|주|개월|년|억|만원|원)"
    )
    return {match.group(0).strip() for match in metric_pattern.finditer(source)}


def _evidence_signature_tokens(question: QuestionSet) -> set[str]:
    source = " ".join(
        _list_from_value(question.get("document_evidence"))
        + [str(question.get("generation_basis") or "")]
    ).lower()
    normalized = re.sub(r"[^0-9a-zA-Z가-힣\s]", " ", source)
    stopwords = {
        "이력서",
        "포트폴리오",
        "자기소개서",
        "경력기술서",
        "프로젝트",
        "경험",
        "사례",
        "설명",
        "질문",
        "검증",
        "지원자",
        "문서",
        "기반",
    }
    return {
        token
        for token in normalized.split()
        if len(token) >= 2 and token not in stopwords
    }


def _question_signature_tokens(question: QuestionSet) -> set[str]:
    source = " ".join(
        [
            str(question.get("category") or ""),
            str(question.get("question_text") or ""),
            str(question.get("generation_basis") or ""),
        ]
    ).lower()
    normalized = re.sub(r"[^0-9a-zA-Z가-힣\s]", " ", source)
    tokens = {token for token in normalized.split() if len(token) >= 2}
    return tokens


def _shares_metric_anchor(candidate: QuestionSet, existing: QuestionSet) -> bool:
    candidate_metrics = _metric_tokens_from_text(
        " ".join(
            [
                str(candidate.get("question_text") or ""),
                str(candidate.get("generation_basis") or ""),
                " ".join(_list_from_value(candidate.get("document_evidence"))),
            ]
        )
    )
    existing_metrics = _metric_tokens_from_text(
        " ".join(
            [
                str(existing.get("question_text") or ""),
                str(existing.get("generation_basis") or ""),
                " ".join(_list_from_value(existing.get("document_evidence"))),
            ]
        )
    )
    return bool(candidate_metrics and existing_metrics and candidate_metrics & existing_metrics)


def _same_verification_axis(candidate: QuestionSet, existing: QuestionSet) -> bool:
    candidate_focus = _focus_area_key(candidate)
    existing_focus = _focus_area_key(existing)
    if candidate_focus and candidate_focus == existing_focus:
        return True
    return bool(candidate.get("category") and candidate.get("category") == existing.get("category"))


def _is_near_duplicate_question(candidate: QuestionSet, selected: list[QuestionSet]) -> bool:
    candidate_key = _question_text_key(candidate.get("question_text"))
    candidate_tokens = _question_signature_tokens(candidate)
    candidate_evidence_tokens = _evidence_signature_tokens(candidate)
    if not candidate_tokens:
        return False

    for existing in selected:
        existing_key = _question_text_key(existing.get("question_text"))
        if candidate_key == existing_key:
            return True
        if SequenceMatcher(None, candidate_key, existing_key).ratio() >= 0.7:
            return True

        existing_tokens = _question_signature_tokens(existing)
        existing_evidence_tokens = _evidence_signature_tokens(existing)
        if not existing_tokens:
            continue

        intersection = len(candidate_tokens & existing_tokens)
        union = len(candidate_tokens | existing_tokens)
        if union == 0:
            continue

        jaccard = intersection / union
        if jaccard >= 0.6:
            return True
        if (
            candidate.get("category") == existing.get("category")
            and intersection >= 3
            and jaccard >= 0.35
        ):
            return True
        if _same_verification_axis(candidate, existing):
            evidence_union = len(candidate_evidence_tokens | existing_evidence_tokens)
            if evidence_union:
                evidence_overlap = len(candidate_evidence_tokens & existing_evidence_tokens) / evidence_union
                if evidence_overlap >= 0.45:
                    return True
            if _shares_metric_anchor(candidate, existing):
                return True
    return False


def _append_unique_note(existing: list[str], note: str) -> list[str]:
    values = [str(item).strip() for item in existing if str(item).strip()]
    if note not in values:
        values.append(note)
    return values


def _apply_overlap_penalties(questions: list[QuestionSet]) -> list[QuestionSet]:
    """Downgrade paraphrased duplicates before the selector sees them."""

    normalized = deepcopy(questions)
    ranked = sorted(normalized, key=_selection_key, reverse=True)
    accepted: list[QuestionSet] = []

    for question in ranked:
        if not _is_selectable(question):
            continue
        if not _is_near_duplicate_question(question, accepted):
            accepted.append(question)
            continue

        question["status"] = "needs_revision"
        question["review_status"] = "needs_revision"
        question["is_selectable"] = False
        question["review_issue_types"] = _append_unique_note(
            _list_from_value(question.get("review_issue_types")),
            "overlap_with_other_questions",
        )
        question["review_risks"] = _append_unique_note(
            _list_from_value(question.get("review_risks")),
            "이미 더 강한 질문이 같은 문서 근거와 검증축을 다루고 있어 최종 질문 세트의 다양성을 해칠 수 있음",
        )
        question["recommended_revision"] = (
            question.get("recommended_revision")
            or "같은 성과나 같은 문서 근거를 반복하지 말고, 다른 근거나 다른 검증축을 찌르는 질문으로 바꿔 주세요."
        )

    return normalized


def _questions_to_evaluate(questions: list[QuestionSet]) -> list[QuestionSet]:
    targets: list[QuestionSet] = []
    for question in questions:
        if question.get("status") in {"pending", "human_rejected"}:
            targets.append(question)
    return targets


def _hard_issue(issue_types: list[str]) -> bool:
    return bool(set(issue_types) & HARD_REVIEW_ISSUES)


def _has_unsupported_ownership_phrase(question: QuestionSet) -> bool:
    question_text = str(question.get("question_text") or "")
    if not question_text:
        return False

    risky_phrases = ("혼자", "단독", "전부", "끝까지 책임")
    if not any(phrase in question_text for phrase in risky_phrases):
        return False

    evidence_text = " ".join(_list_from_value(question.get("document_evidence")))
    supported_markers = ("혼자", "단독", "1인", "전담", "전 과정", "end-to-end", "엔드투엔드")
    return not any(marker in evidence_text for marker in supported_markers)


def _is_candidate_choice_prompt(question: QuestionSet) -> bool:
    question_text = str(question.get("question_text") or "")
    candidate_choice_markers = (
        "가장 자신 있는",
        "하나를 골라",
        "두 가지를 골라",
        "편한 사례를 골라",
        "원하는 사례를 골라",
    )
    return any(marker in question_text for marker in candidate_choice_markers)


def _is_easy_escape_prompt(question: QuestionSet) -> bool:
    question_text = str(question.get("question_text") or "")
    fallback_markers = ("없다면", "없으면", "없을 경우", "없더라도")
    if any(marker in question_text for marker in fallback_markers):
        return False
    escape_markers = (
        "있다면",
        "있으시다면",
        "있다면 말씀해 주세요",
        "있다면 설명해 주세요",
    )
    return any(marker in question_text for marker in escape_markers)


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

    if _has_unsupported_ownership_phrase(updated):
        issue_types = list(updated.get("review_issue_types") or [])
        if "unsupported_assumption" not in issue_types:
            issue_types.append("unsupported_assumption")
        risks = list(updated.get("review_risks") or [])
        risks.append("문서 근거 없이 단독 수행/전면 책임을 전제한 표현이 포함됨")
        updated.update(
            {
                "status": "needs_revision",
                "review_status": "needs_revision",
                "review_issue_types": issue_types,
                "review_risks": risks,
                "is_selectable": False,
            }
        )

    if _is_candidate_choice_prompt(updated):
        issue_types = list(updated.get("review_issue_types") or [])
        if "no_document_anchor" not in issue_types:
            issue_types.append("no_document_anchor")
        risks = list(updated.get("review_risks") or [])
        risks.append("문서의 구체 근거를 찌르지 않고 지원자에게 검증 대상을 고르게 함")
        updated.update(
            {
                "status": "needs_revision",
                "review_status": "needs_revision",
                "review_issue_types": issue_types,
                "review_risks": risks,
                "is_selectable": False,
            }
        )

    if _is_easy_escape_prompt(updated):
        risks = list(updated.get("review_risks") or [])
        risks.append("'없습니다' 한마디로 답변이 끝날 가능성이 있는 질문 구조")
        updated.update(
            {
                "review_risks": risks,
                "is_selectable": False,
            }
        )
        if updated.get("review_status") == "approved":
            updated["status"] = "needs_revision"
            updated["review_status"] = "needs_revision"
    return updated


def _fallback_review(question: QuestionSet, reason: str) -> ReviewResult:
    return ReviewResult(
        status="rejected",
        reason=reason,
        recommended_revision="질문과 평가가이드가 문서 근거와 직무 역량을 더 명확히 연결하도록 보완하세요.",
        issue_types=["reviewer_fallback"],
        requested_revision_fields=["question_text", "evaluation_guide"],
        question_quality_scores=QuestionQualityRubric(
            job_relevance=1,
            document_grounding=1,
            competency_signal=1,
            specificity=1,
            clarity=1,
        ),
        evaluation_guide_scores=EvaluationGuideRubric(
            scoring_clarity=1,
            evidence_alignment=1,
            answer_discriminability=1,
            risk_awareness=1,
            interviewer_usability=1,
        ),
        overall_score=1.0,
        selection_reason="리뷰어 실패 질문은 자동 선별 대상에서 제외했습니다.",
        strengths=[],
        risks=["reviewer_fallback"],
        is_selectable=False,
    )


def _is_selectable(question: QuestionSet) -> bool:
    if question.get("status") == "rejected" or question.get("review_status") == "rejected":
        return False
    if question.get("is_selectable") is False:
        return False
    return float(question.get("score") or 0) >= MIN_SELECTABLE_SCORE


def _is_people_focus(question: QuestionSet) -> bool:
    focus_area = str(question.get("focus_area") or "").strip().lower()
    if focus_area in PEOPLE_FOCUS_AREAS:
        return True
    category = str(question.get("category") or "")
    people_keywords = (
        "협업",
        "갈등",
        "커뮤니케이션",
        "소통",
        "피드백",
        "조직",
        "적응",
        "인성",
        "문화",
        "책임감",
    )
    return any(keyword in category for keyword in people_keywords)


def _selection_key(question: QuestionSet) -> tuple[float, float, float, int, int]:
    status_bonus = 0.35 if question.get("review_status") == "approved" else 0.0
    evidence_bonus = 0.15 if question.get("document_evidence") else 0.0
    compound_penalty = 0.5 if _is_multi_track_question_text(question.get("question_text")) else 0.0
    score = float(question.get("score") or 0)
    quality = float(question.get("question_quality_average") or 0)
    guide = float(question.get("evaluation_guide_average") or 0)
    risk_penalty = len(question.get("review_risks", []) or [])
    issue_penalty = len(question.get("review_issue_types", []) or [])
    return (
        score + status_bonus + evidence_bonus - compound_penalty,
        quality,
        guide,
        -risk_penalty,
        -issue_penalty,
    )


def _must_ask_focus_areas(verification_profile: dict[str, Any] | None) -> set[str]:
    if not verification_profile:
        return set()
    points = verification_profile.get("must_verify_points") or []
    focus_areas: set[str] = set()
    for point in points:
        if not isinstance(point, dict):
            continue
        if point.get("must_ask"):
            dimension = str(point.get("dimension") or "").strip().lower()
            if dimension:
                focus_areas.add(dimension)
    return focus_areas


def _must_ask_points(verification_profile: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not verification_profile:
        return []
    points = verification_profile.get("must_verify_points") or []
    return [
        point
        for point in points
        if isinstance(point, dict) and point.get("must_ask")
    ]


def _must_ask_signal_hints(signal_type: str) -> tuple[str, ...]:
    mapping = {
        "return_to_work_readiness": ("공백기", "복귀", "산출물", "준비", "재현 가능한"),
        "gap_without_artifact": ("공백기", "산출물", "없다면", "검증", "준비"),
        "metric_ownership": ("측정", "기여", "수치", "성과", "분리"),
        "career_transition_evidence": ("전환", "보완", "준비", "실행 근거"),
        "transition_reason_present": ("전환", "이유", "실행 근거", "보완"),
        "transition_reason_missing": ("전환", "왜", "준비", "증거"),
        "learning_without_strong_artifact": ("학습", "검증", "산출물", "프로젝트"),
    }
    return mapping.get(signal_type, ())


def _question_matches_must_ask_point(question: QuestionSet, point: dict[str, Any]) -> bool:
    if _focus_area_key(question) != str(point.get("dimension") or "").strip().lower():
        return False

    question_text = " ".join(
        [
            str(question.get("question_text") or ""),
            str(question.get("generation_basis") or ""),
            " ".join(_list_from_value(question.get("document_evidence"))),
        ]
    ).lower()
    point_evidence = str(point.get("evidence") or "")
    point_tokens = {
        token
        for token in re.sub(r"[^0-9a-zA-Z가-힣\s]", " ", point_evidence.lower()).split()
        if len(token) >= 2
    }
    question_tokens = _evidence_signature_tokens(question) | _question_signature_tokens(question)

    if point_tokens:
        overlap = len(point_tokens & question_tokens) / len(point_tokens | question_tokens)
        if overlap >= 0.2:
            return True

    if _metric_tokens_from_text(point_evidence) & _metric_tokens_from_text(question_text):
        return True

    signal_type = str(point.get("signal_type") or "")
    hints = _must_ask_signal_hints(signal_type)
    return bool(hints and all(hint.lower() in question_text for hint in hints[:2]))


def _focus_area_cap(question: QuestionSet, requested_count: int) -> int:
    if requested_count < 5:
        return requested_count

    focus_area = _focus_area_key(question)
    if focus_area == "technical_depth":
        return 2
    if focus_area in {"performance_ownership", "career_context", "growth_adaptability"}:
        return 1
    if focus_area in PEOPLE_FOCUS_AREAS:
        return 1
    return 1


def _can_add_question(
    question: QuestionSet,
    selected: list[QuestionSet],
    seen_categories: set[str],
    ranked_count: int,
    requested_count: int,
    *,
    allow_seen_category: bool = False,
    allow_focus_cap: bool = False,
) -> bool:
    if requested_count >= 5 and _is_people_focus(question) and any(
        _is_people_focus(item) for item in selected
    ):
        return False

    focus_area = _focus_area_key(question)
    if focus_area and not allow_focus_cap:
        current_focus_count = len(
            [item for item in selected if _focus_area_key(item) == focus_area]
        )
        if current_focus_count >= _focus_area_cap(question, requested_count):
            return False

    category = str(question.get("category") or "")
    if (
        not allow_seen_category
        and category in seen_categories
        and ranked_count >= requested_count + 2
    ):
        return False

    return not _is_near_duplicate_question(question, selected)


def select_top_questions(
    questions: list[QuestionSet],
    requested_count: int,
    verification_profile: dict[str, Any] | None = None,
) -> list[QuestionSet]:
    eligible = _apply_overlap_penalties(
        [question for question in questions if _is_selectable(question)]
    )
    ranked = sorted(eligible, key=_selection_key, reverse=True)
    must_ask_focus_areas = _must_ask_focus_areas(verification_profile)
    must_ask_points = _must_ask_points(verification_profile)

    selected: list[QuestionSet] = []
    seen_categories: set[str] = set()
    selected_ids: set[str] = set()

    # Keep room for one collaboration/culture-fit question, but only if that
    # question is actually strong enough to survive in a real interview set.
    if requested_count >= 5:
        people_candidates = [
            question
            for question in ranked
            if _is_people_focus(question)
            and float(question.get("score") or 0) >= STRONG_SELECTABLE_SCORE
        ]
        for question in people_candidates:
            if not _can_add_question(
                question,
                selected,
                seen_categories,
                len(ranked),
                requested_count,
            ):
                continue
            selected.append(question)
            selected_ids.add(str(question.get("id")))
            seen_categories.add(str(question.get("category") or ""))
            break

    # Protect concrete must-ask verification points first so a duplicated
    # technical/performance question cannot push out a real must-check item.
    for point in must_ask_points:
        for question in ranked:
            if str(question.get("id")) in selected_ids:
                continue
            if not _question_matches_must_ask_point(question, point):
                continue
            if not _can_add_question(
                question,
                selected,
                seen_categories,
                len(ranked),
                requested_count,
            ):
                continue
            selected.append(question)
            selected_ids.add(str(question.get("id")))
            seen_categories.add(str(question.get("category") or ""))
            break

    # If a must-ask focus area still has no representative, protect one slot
    # for that axis before the general ranking fills the set.
    for focus_area in ("performance_ownership", "career_context", "growth_adaptability"):
        if focus_area not in must_ask_focus_areas:
            continue
        if any(_focus_area_key(item) == focus_area for item in selected):
            continue
        for question in ranked:
            if str(question.get("id")) in selected_ids:
                continue
            if _focus_area_key(question) != focus_area:
                continue
            if not _can_add_question(
                question,
                selected,
                seen_categories,
                len(ranked),
                requested_count,
            ):
                continue
            selected.append(question)
            selected_ids.add(str(question.get("id")))
            seen_categories.add(str(question.get("category") or ""))
            break

    for question in ranked:
        if str(question.get("id")) in selected_ids:
            continue
        if not _can_add_question(
            question,
            selected,
            seen_categories,
            len(ranked),
            requested_count,
        ):
            continue
        selected.append(question)
        selected_ids.add(str(question.get("id")))
        seen_categories.add(str(question.get("category") or ""))
        if len(selected) >= requested_count:
            break

    if len(selected) < requested_count:
        for question in ranked:
            if str(question.get("id")) in selected_ids:
                continue
            if not _can_add_question(
                question,
                selected,
                seen_categories,
                len(ranked),
                requested_count,
                allow_seen_category=True,
            ):
                continue
            selected.append(question)
            selected_ids.add(str(question.get("id")))
            seen_categories.add(str(question.get("category") or ""))
            if len(selected) >= requested_count:
                break

    if len(selected) < requested_count:
        for question in ranked:
            if str(question.get("id")) in selected_ids:
                continue
            if _is_near_duplicate_question(question, selected) and len(ranked) > requested_count:
                continue
            selected.append(question)
            selected_ids.add(str(question.get("id")))
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
        selected_targets = select_top_questions(
            targets,
            max(1, len(target_ids)),
            state.get("verification_profile"),
        )
        if selected_targets:
            return selected_targets
    return state.get("selected_questions") or select_top_questions(
        questions,
        requested_count,
        state.get("verification_profile"),
    )


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
            f"[프롬프트 프로필]\n{_clip_text(state.get('prompt_profile_summary'), 4000)}",
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


async def verification_point_extractor_node(state: AgentState) -> AgentState:
    if state.get("verification_profile"):
        return {**state, "llm_usages": []}

    errors = list(state.get("errors") or [])
    raw_outputs = dict(state.get("raw_outputs") or {})
    heuristic_profile = _heuristic_verification_profile(state)
    prompt = VERIFICATION_EXTRACTOR_USER_PROMPT.format(
        job_posting=state.get("job_posting") or "",
        candidate_context=state.get("candidate_context") or _candidate_context(state),
        heuristic_signals=_safe_json(heuristic_profile),
    )

    try:
        output, usages = await call_structured_output_with_usage(
            node_name="verification_point_extractor",
            system_prompt=VERIFICATION_EXTRACTOR_SYSTEM_PROMPT,
            user_prompt=prompt,
            response_model=VerificationProfileOutput,
        )
    except StructuredOutputCallError as exc:
        errors.append(f"verification_point_extractor 호출 실패: {exc}")
        fallback = VerificationProfileOutput(
        )
        merged = _merge_verification_profiles(
            fallback.model_dump(mode="json"), heuristic_profile
        )
        return {
            **state,
            "verification_profile": merged,
            "errors": errors,
            "raw_outputs": raw_outputs,
            "llm_usages": exc.usages,
        }
    except Exception as exc:  # noqa: BLE001
        errors.append(f"verification_point_extractor 호출 실패: {exc}")
        fallback = VerificationProfileOutput()
        merged = _merge_verification_profiles(
            fallback.model_dump(mode="json"), heuristic_profile
        )
        return {
            **state,
            "verification_profile": merged,
            "errors": errors,
            "raw_outputs": raw_outputs,
        }

    merged_output = _merge_verification_profiles(
        output.model_dump(mode="json"), heuristic_profile
    )
    raw_outputs["verification_point_extractor"] = {
        "heuristic_seed": heuristic_profile,
        "output": output.model_dump(mode="json"),
        "merged_output": merged_output,
    }
    return {
        **state,
        "verification_profile": merged_output,
        "errors": errors,
        "raw_outputs": raw_outputs,
        "llm_usages": usages,
    }


async def questioner_node(state: AgentState) -> AgentState:
    errors = list(state.get("errors") or [])
    raw_outputs = dict(state.get("raw_outputs") or {})
    mode = _generation_mode(state)
    questions = deepcopy(state.get("questions") or [])

    prompt = QUESTIONER_USER_PROMPT.format(
        job_posting=state.get("job_posting") or "",
        prompt_profile_summary=_prompt_profile_summary(state),
        candidate_context=state.get("candidate_context") or _candidate_context(state),
        verification_profile=_verification_profile_for_prompt(state),
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
        target_question_feedback=_target_question_feedback(state),
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
            "llm_usages": exc.usages,
            "status": "failed",
        }
    except Exception as exc:  # noqa: BLE001
        errors.append(f"questioner 호출 실패: {exc}")
        return {
            **state,
            "errors": errors,
            "raw_outputs": raw_outputs,
            "llm_usages": [],
            "status": "failed",
        }

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
        "llm_usages": usages,
        "status": "pending",
    }


async def predictor_node(state: AgentState) -> AgentState:
    errors = list(state.get("errors") or [])
    raw_outputs = dict(state.get("raw_outputs") or {})
    questions = deepcopy(state.get("questions") or [])
    targets = [question for question in questions if not question.get("predicted_answer")]
    if not targets:
        return {**state, "llm_usages": []}

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
            "llm_usages": exc.usages,
        }
    except Exception as exc:  # noqa: BLE001
        errors.append(f"predictor 호출 실패: {exc}")
        return {**state, "errors": errors, "raw_outputs": raw_outputs, "llm_usages": []}

    raw_outputs["predictor"] = {"output": output.model_dump(mode="json")}

    by_id = {
        str(answer.question_id): answer
        for answer in output.answers
        if isinstance(answer, PredictedAnswer) and str(answer.question_id).strip()
    }
    for question in questions:
        answer = by_id.get(str(question.get("id")))
        if not answer:
            continue
        question["predicted_answer"] = _compact_sentences(
            answer.predicted_answer,
            max_sentences=3,
            limit=PREDICTED_ANSWER_LIMIT,
        )
        question["predicted_answer_basis"] = _compact_sentences(
            answer.predicted_answer_basis,
            max_sentences=2,
            limit=PREDICTED_BASIS_LIMIT,
        )

    return {
        **state,
        "questions": questions,
        "errors": errors,
        "raw_outputs": raw_outputs,
        "llm_usages": usages,
    }


async def driller_node(state: AgentState) -> AgentState:
    errors = list(state.get("errors") or [])
    raw_outputs = dict(state.get("raw_outputs") or {})
    questions = deepcopy(state.get("questions") or [])
    targets = [question for question in questions if not question.get("follow_up_questions")]
    if not targets:
        return {**state, "llm_usages": []}

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
            "llm_usages": exc.usages,
        }
    except Exception as exc:  # noqa: BLE001
        errors.append(f"driller 호출 실패: {exc}")
        return {**state, "errors": errors, "raw_outputs": raw_outputs, "llm_usages": []}

    raw_outputs["driller"] = {"output": output.model_dump(mode="json")}

    by_id = {
        str(item.question_id): item
        for item in output.follow_ups
        if str(item.question_id).strip()
    }
    for question in questions:
        item = by_id.get(str(question.get("id")))
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
        "llm_usages": usages,
    }


async def reviewer_node(state: AgentState) -> AgentState:
    errors = list(state.get("errors") or [])
    raw_outputs = dict(state.get("raw_outputs") or {})
    questions = deepcopy(state.get("questions") or [])
    targets = _questions_to_evaluate(questions)
    requested = _requested_count(state)

    if not targets:
        selected = select_top_questions(
            questions,
            requested,
            state.get("verification_profile"),
        )
        return {
            **state,
            "selected_questions": selected,
            "is_all_approved": all(q.get("review_status") == "approved" for q in selected),
            "questions": questions,
            "errors": errors,
            "raw_outputs": raw_outputs,
            "llm_usages": [],
        }

    prompt = REVIEWER_USER_PROMPT.format(
        job_posting=state.get("job_posting") or "",
        prompt_profile_summary=_prompt_profile_summary(state),
        candidate_context=state.get("candidate_context") or _candidate_context(state),
        verification_profile=_verification_profile_for_prompt(state),
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
                    question_id=str(question.get("id") or ""),
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
                    question_id=str(question.get("id") or ""),
                    question_text=question.get("question_text") or "",
                    review=_fallback_review(question, "리뷰어 호출 실패"),
                )
                for question in targets
            ]
        )
        usages = []

    raw_outputs["reviewer"] = {"output": output.model_dump(mode="json")}
    reviews_by_id = {
        str(item.question_id): item.review
        for item in output.reviews
        if isinstance(item, ReviewedQuestion) and str(item.question_id).strip()
    }

    updates: dict[str, QuestionSet] = {}
    for question in targets:
        review = reviews_by_id.get(str(question.get("id")))
        if review is None:
            review = _fallback_review(question, "리뷰어가 해당 질문 평가를 반환하지 않았습니다.")
        updates[str(question.get("id"))] = _review_to_question(question, review)

    merged = _apply_overlap_penalties(_merge_question_lists(questions, updates))
    selected = select_top_questions(
        merged,
        requested,
        state.get("verification_profile"),
    )
    return {
        **state,
        "questions": merged,
        "selected_questions": selected,
        "is_all_approved": all(q.get("review_status") == "approved" for q in selected),
        "errors": errors,
        "raw_outputs": raw_outputs,
        "llm_usages": usages,
    }


def review_router(state: AgentState) -> str:
    if state.get("status") == "failed":
        return "end"

    requested = _requested_count(state)
    selected = state.get("selected_questions") or select_top_questions(
        state.get("questions") or [],
        requested,
        state.get("verification_profile"),
    )
    retry_count = int(state.get("retry_count") or 0)
    max_retry = int(state.get("max_retry_count") or MAX_RETRY_COUNT)

    if len(selected) >= requested:
        enough_quality, _, _ = _quality_gate(selected, requested)
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
    enough_quality, average_score, approved_count = _quality_gate(selected, requested)

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
    elif enough_selected and enough_quality:
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
            "job_fit": "지원자 문서와 채용공고 및 프롬프트 프로필을 근거로 면접 질문 후보를 평가하고 상위 질문을 선별했습니다.",
            "risks": errors
            + (
                []
                if enough_quality or not items
                else [
                    f"품질 게이트 미통과: average_score={average_score}, approved_count={approved_count}"
                ]
            ),
        },
        generation_metadata={
            "candidate_count": len(questions),
            "selected_count": len(items),
            "retry_count": retry_count,
            "average_selected_score": average_score,
            "quality_gate_passed": enough_quality,
            "required_approved_count": min(3, requested),
            "approved_selected_count": len(
                [item for item in items if item.review.status == "approved"]
            ),
            "approved_count": approved_count,
            "all_selected_approved": all(
                item.review.status == "approved" for item in items
            )
            if items
            else False,
            "selection_policy": "reviewer_scores_all_candidates_selector_returns_top_n",
        },
    )
