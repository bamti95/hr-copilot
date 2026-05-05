"""Question state and selection helpers for the JH interview graph."""

from __future__ import annotations

from typing import Any

from ai.interview_graph_JH.config import (
    ADD_QUESTION_COUNT,
    DEFAULT_CANDIDATE_QUESTION_COUNT,
    DEFAULT_SELECTED_QUESTION_COUNT,
    MAX_DOCUMENT_CHARS,
    MAX_QUESTION_TEXT_CHARS,
    MORE_QUESTION_COUNT,
)
from ai.interview_graph_JH.content_utils import (
    clip_question_text,
    normalize_document_evidence,
    normalize_evaluation_guide,
    to_json,
)
from ai.interview_graph_JH.state import AgentState, QuestionSet


def recruitment_criteria(state: AgentState) -> str:
    prompt_profile = state.get("prompt_profile") or {}
    return str(prompt_profile.get("system_prompt") or "채용 기준이 별도로 제공되지 않았습니다.")


def difficulty_bucket(state: AgentState) -> str:
    raw = str(state.get("difficulty_level") or "").strip().upper()
    if raw in {"JUNIOR", "INTERN", "NEW_GRAD", "ENTRY"}:
        return "JUNIOR"
    if raw in {"MID", "SENIOR", "LEAD", "STAFF", "PRINCIPAL"}:
        return "EXPERIENCED"
    return "GENERAL"


def difficulty_guidance(state: AgentState) -> str:
    bucket = difficulty_bucket(state)
    if bucket == "JUNIOR":
        return (
            "지원자를 주니어로 보고 학습 능력, 프로젝트 수행 방식, 문제 해결 접근, 기본기를 중심으로 질문하라."
        )
    if bucket == "EXPERIENCED":
        return (
            "지원자를 경력직으로 보고 실제 업무 경험, 역할 범위, 의사결정, 성과 검증을 중심으로 질문하라."
        )
    return "난이도가 명확하지 않으므로 문서 기반 경험 검증과 기본 역량 검증의 균형을 맞춰라."


def merge_document_text(state: AgentState) -> str:
    sections = [
        "[session]",
        f"session_id: {state.get('session_id')}",
        f"target_job: {state.get('target_job')}",
        f"difficulty_level: {state.get('difficulty_level')}",
        "",
        "[candidate]",
        f"candidate_id: {state.get('candidate_id')}",
        f"name: {state.get('candidate_name')}",
    ]
    documents = list(state.get("documents") or [])
    if not documents:
        return "\n".join(sections)

    reserved = len("\n".join(sections)) + len(documents) * 64
    per_doc_budget = max(600, (MAX_DOCUMENT_CHARS - reserved) // len(documents))

    for document in documents:
        extracted_text = str(document.get("extracted_text") or "").strip()
        clipped = extracted_text[:per_doc_budget]
        sections.extend(
            [
                "",
                f"[document #{document.get('document_id')}]",
                f"type: {document.get('document_type')}",
                f"title: {document.get('title')}",
                clipped or "(추출 텍스트 없음)",
            ]
        )

    return "\n".join(sections)[:MAX_DOCUMENT_CHARS]


def format_questions(
    items: list[QuestionSet],
    *,
    include_answer: bool = False,
    include_retry_feedback: bool = True,
) -> str:
    if not items:
        return "(없음)"
    compact: list[dict[str, Any]] = []
    for item in items:
        data: dict[str, Any] = {
            "id": item.get("id"),
            "category": item.get("category"),
            "question_text": item.get("question_text"),
            "generation_basis": item.get("generation_basis"),
            "document_evidence": normalize_document_evidence(item.get("document_evidence", [])),
            "evaluation_guide": item.get("evaluation_guide"),
            "risk_tags": item.get("risk_tags", []),
            "competency_tags": item.get("competency_tags", []),
            "status": item.get("status"),
        }
        if include_retry_feedback:
            data.update(
                {
                    "reject_reason": item.get("reject_reason") or item.get("recommended_revision"),
                    "review_issue_types": item.get("review_issue_types", []),
                    "requested_revision_fields": item.get("requested_revision_fields", []),
                    "retry_issue_types": item.get("retry_issue_types", []),
                    "regen_targets": item.get("regen_targets", []),
                    "retry_guidance": item.get("retry_guidance", ""),
                }
            )
        if include_answer:
            data.update(
                {
                    "predicted_answer": item.get("predicted_answer"),
                    "predicted_answer_basis": item.get("predicted_answer_basis"),
                    "answer_confidence": item.get("answer_confidence"),
                    "answer_risk_points": item.get("answer_risk_points", []),
                    "follow_up_question": item.get("follow_up_question"),
                    "follow_up_basis": item.get("follow_up_basis"),
                    "drill_type": item.get("drill_type"),
                }
            )
        compact.append(data)
    return to_json(compact)


def normalized_question_text(question: QuestionSet) -> str:
    return " ".join(str(question.get("question_text") or "").split()).lower()


def is_approved_question(question: QuestionSet) -> bool:
    status = str(question.get("status") or question.get("review_status") or "").strip()
    return status == "approved"


def question_id(question: QuestionSet, index: int) -> str:
    return str(question.get("id") or f"q-{index + 1}")


def allocate_question_id(used_ids: set[str], counter: list[int]) -> str:
    while True:
        counter[0] += 1
        candidate = f"q-{counter[0]}"
        if candidate not in used_ids:
            used_ids.add(candidate)
            return candidate


def ensure_question_ids(questions: list[QuestionSet]) -> None:
    used_ids: set[str] = set()
    max_seen = 0
    for question in questions:
        current_id = str(question.get("id") or "")
        if not current_id:
            continue
        used_ids.add(current_id)
        if current_id.startswith("q-"):
            try:
                max_seen = max(max_seen, int(current_id.removeprefix("q-")))
            except ValueError:
                continue

    counter = [max_seen]
    for question in questions:
        if not question.get("id"):
            question["id"] = allocate_question_id(used_ids, counter)


def default_regen_targets(question: QuestionSet) -> list[str]:
    requested = [str(item) for item in question.get("regen_targets") or [] if str(item).strip()]
    if requested:
        return requested
    requested = [str(item) for item in question.get("requested_revision_fields") or [] if str(item).strip()]
    return requested or ["question_text", "evaluation_guide"]


def should_refresh_predicted_answer(question: QuestionSet) -> bool:
    targets = set(default_regen_targets(question))
    if not question.get("predicted_answer"):
        return True
    return bool({"question_text", "generation_basis", "document_evidence", "predicted_answer"} & targets)


def should_refresh_follow_up(question: QuestionSet) -> bool:
    targets = set(default_regen_targets(question))
    if not question.get("follow_up_question"):
        return True
    return bool(
        {
            "question_text",
            "generation_basis",
            "document_evidence",
            "predicted_answer",
            "follow_up_question",
        }
        & targets
    )


def requested_question_count(state: AgentState) -> int:
    mode = state.get("generation_mode")
    if mode == "more":
        return MORE_QUESTION_COUNT
    if mode == "add_question":
        return ADD_QUESTION_COUNT
    return DEFAULT_SELECTED_QUESTION_COUNT


def select_top_questions(
    questions: list[QuestionSet],
    *,
    limit: int,
) -> list[QuestionSet]:
    if not questions:
        return []

    unique_questions: list[QuestionSet] = []
    seen_texts: set[str] = set()
    for question in questions:
        text_key = normalized_question_text(question)
        if not text_key or text_key in seen_texts:
            continue
        seen_texts.add(text_key)
        unique_questions.append(question)

    sorted_questions = sorted(
        unique_questions,
        key=lambda question: (
            is_approved_question(question),
            float(question.get("score") or 0.0),
            bool(question.get("document_evidence")),
            bool(question.get("risk_tags")),
            len(question.get("document_evidence") or []),
        ),
        reverse=True,
    )

    selected: list[QuestionSet] = []
    used_categories: set[str] = set()
    for question in sorted_questions:
        if len(selected) >= limit:
            break
        category = str(question.get("category") or "OTHER")
        if category in used_categories and len(selected) < min(limit, 3):
            continue
        selected.append(question)
        used_categories.add(category)

    for question in sorted_questions:
        if len(selected) >= limit:
            break
        if question not in selected:
            selected.append(question)

    return selected


def selected_questions_for_output(state: AgentState) -> list[QuestionSet]:
    return select_top_questions(
        list(state.get("questions") or []),
        limit=requested_question_count(state),
    )


def questioner_mode(state: AgentState, questions: list[QuestionSet]) -> tuple[str, list[QuestionSet]]:
    rewrite_targets = [
        item
        for item in questions
        if item.get("status") in {"rejected", "needs_revision"}
    ]
    if rewrite_targets:
        has_partial = any(default_regen_targets(item) for item in rewrite_targets)
        return ("partial_rewrite" if has_partial else "rewrite"), rewrite_targets

    human_action = (state.get("human_action") or "").strip()
    target_ids = {str(qid) for qid in (state.get("target_question_ids") or [])}
    if human_action in {"regenerate", "regenerate_question"} and target_ids:
        targets = [item for item in questions if str(item.get("id") or "") in target_ids]
        has_partial = any(default_regen_targets(item) for item in targets)
        return ("partial_rewrite" if has_partial else "rewrite"), targets
    if human_action in {"more", "more_questions"}:
        return "more", []
    if human_action in {"add_question", "generate_follow_up", "risk_questions", "different_perspective"}:
        return "add_question", []
    return "initial", []


def task_instruction(mode: str, targets: list[QuestionSet]) -> str:
    if mode == "initial":
        return (
            f"총 면접 질문 후보 {DEFAULT_CANDIDATE_QUESTION_COUNT}개를 생성하라. "
            f"모든 question_text는 {MAX_QUESTION_TEXT_CHARS}자 이내로 유지하고 실제 면접에서 바로 읽을 수 있게 작성하라. "
            "질문 후보들은 서로 역할이 겹치지 않게 분산하라. "
            "가능하면 성과 검증, 실패/학습, 협업/조율, 우선순위/압박 대응, 직무 적합성 중 서로 다른 축을 우선 배치하라. "
            "문서에 없는 정량 성과나 도구 활용을 먼저 가정하지 말고, 실제로 했는지 확인하는 질문을 먼저 만들라."
        )
    if mode == "more":
        return (
            f"기존 질문과 중복되지 않는 추가 질문 {MORE_QUESTION_COUNT}개를 생성하라. "
            f"모든 question_text는 {MAX_QUESTION_TEXT_CHARS}자 이내로 유지하라. "
            "기존 질문과 같은 검증 축을 반복하지 말고 비어 있는 핵심 역량을 보완하라."
        )
    if mode == "add_question":
        return (
            f"추가 지시사항을 반영한 질문 {ADD_QUESTION_COUNT}개를 생성하라. "
            f"모든 question_text는 {MAX_QUESTION_TEXT_CHARS}자 이내로 유지하라. "
            "문서에 없는 정량 수치나 도구 사용을 새로 가정하지 말라."
        )

    target_block = format_questions(targets, include_answer=True)
    return (
        "지정한 질문만 수정하고, 나머지 질문은 유지하라. "
        "regen_targets에 포함된 필드는 이전 시도와 다르게 다시 작성하라. "
        "predicted_answer는 사실 확정이 아니라 조심스러운 추정으로 유지하고, "
        "follow_up_question은 가장 중요한 검증 포인트 하나만 묻는 1문장으로 작성하라. "
        "evaluation_guide는 반드시 상/중/하 3줄 형식으로 작성하라. "
        "문서에 없는 정량 수치, 기간, 비율을 새로 가정하지 말고 실제 행동과 결과 확인을 우선하라.\n"
        f"{target_block}"
    )


def build_question_entry(
    model: dict[str, Any],
    *,
    question_id: str,
    generation_mode: str,
    existing: QuestionSet | None = None,
    requested_fields: list[str] | None = None,
) -> QuestionSet:
    question_text = clip_question_text(model.get("question_text") or "")
    retry_issue_types = list(
        (existing or {}).get("retry_issue_types")
        or (existing or {}).get("review_issue_types")
        or []
    )
    return {
        "id": question_id,
        "category": model.get("category") or (existing or {}).get("category") or "OTHER",
        "generation_basis": model.get("generation_basis") or (existing or {}).get("generation_basis") or "",
        "document_evidence": normalize_document_evidence(
            model.get("document_evidence") or list((existing or {}).get("document_evidence") or [])
        ),
        "question_text": question_text or (existing or {}).get("question_text") or "",
        "evaluation_guide": normalize_evaluation_guide(
            model.get("evaluation_guide") or (existing or {}).get("evaluation_guide") or ""
        ),
        "predicted_answer": "",
        "predicted_answer_basis": "",
        "answer_confidence": "",
        "answer_risk_points": [],
        "follow_up_question": "",
        "follow_up_basis": "",
        "drill_type": "",
        "risk_tags": model.get("risk_tags") or list((existing or {}).get("risk_tags") or []),
        "competency_tags": model.get("competency_tags") or list((existing or {}).get("competency_tags") or []),
        "review_status": "",
        "review_reason": "",
        "reject_reason": "",
        "recommended_revision": "",
        "review_issue_types": [],
        "requested_revision_fields": [],
        "question_quality_scores": {},
        "evaluation_guide_scores": {},
        "question_quality_average": 0.0,
        "evaluation_guide_average": 0.0,
        "score": 0.0,
        "score_reason": "",
        "status": "pending",
        "regen_targets": list(requested_fields or []),
        "generation_mode": generation_mode,
        "retry_issue_types": retry_issue_types,
        "retry_guidance": str((existing or {}).get("retry_guidance") or ""),
    }
