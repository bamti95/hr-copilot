"""면접 질문 그래프의 핵심 노드 모음.

이 파일은 그래프 안에서 실제로 데이터를 가공하는 로직을 담고 있다.
흐름은 아래와 같다.

1. prepare_context: 문서와 세션 정보를 합쳐 공통 문맥을 만든다.
2. questioner: 질문을 생성하거나, 기존 질문을 수정한다.
3. predictor: 지원자가 어떻게 답할지 예상 답변을 만든다.
4. driller: 꼬리질문을 만든다.
5. reviewer: 질문 품질을 루브릭으로 검토한다.

주니어 개발자가 볼 때 중요한 포인트는
"각 노드는 state 전체를 새로 만드는 게 아니라, 필요한 필드만 업데이트한다"는 점이다.
"""

import json
import logging
from typing import Any

from ai.interview_graph_JH.llm_usage import (
    StructuredOutputCallError,
    call_structured_output_with_usage,
)
from ai.interview_graph_JH.schemas import (
    DocumentAnalysisOutput,
    DrillerOutput,
    EvaluationGuideRubric,
    FollowUpQuestion,
    InterviewQuestionItem,
    PredictedAnswer,
    PredictorOutput,
    QuestionCandidate,
    QuestionGenerationResponse,
    QuestionerOutput,
    QuestionQualityRubric,
    ReviewResult,
    ReviewerOutput,
)
from ai.interview_graph_JH import prompts
from ai.interview_graph_JH.state import AgentState, QuestionSet

logger = logging.getLogger(__name__)

MAX_DOCUMENT_CHARS = 18000
PREDICTOR_DOCUMENT_CHARS = 7000
DEFAULT_QUESTION_COUNT = 5
MORE_QUESTION_COUNT = 3
ADD_QUESTION_COUNT = 2
MAX_QUESTION_TEXT_CHARS = 180
MAX_FOLLOW_UP_CHARS = 160
MAX_PREDICTED_ANSWER_CHARS = 170
QUESTION_QUALITY_KEYS = [
    "job_relevance",
    "document_grounding",
    "validation_power",
    "specificity",
    "distinctiveness",
    "interview_usability",
    "core_resume_coverage",
]
EVALUATION_GUIDE_KEYS = [
    "guide_alignment",
    "signal_clarity",
    "good_bad_answer_separation",
    "practical_usability",
    "verification_specificity",
]


def _json(value: Any) -> str:
    """프롬프트에 넣기 쉽게 dict/list를 JSON 문자열로 바꾼다."""
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _clip(value: str, max_chars: int) -> str:
    """너무 긴 텍스트를 잘라 프롬프트 길이를 제어한다."""
    text = value.strip()
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars]}\n\n...(길이 제한으로 일부 생략)"


def _clip_question_text(value: str) -> str:
    """질문 본문은 실제 면접에서 읽기 쉬워야 하므로 길이를 강하게 제한한다."""
    text = " ".join(str(value or "").split())
    if len(text) <= MAX_QUESTION_TEXT_CHARS:
        return text
    clipped = text[: MAX_QUESTION_TEXT_CHARS - 1].rstrip()
    return f"{clipped}..."


def _clip_follow_up_text(value: str) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= MAX_FOLLOW_UP_CHARS:
        return text
    clipped = text[: MAX_FOLLOW_UP_CHARS - 1].rstrip()
    return f"{clipped}..."


def _normalize_document_evidence(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = [text]
        else:
            if not isinstance(parsed, list):
                parsed = [parsed]
    elif isinstance(value, list):
        parsed = value
    else:
        parsed = [value]

    normalized: list[str] = []
    seen: set[str] = set()
    for item in parsed:
        text = " ".join(str(item or "").split()).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return normalized


def _normalize_predicted_answer(value: str) -> str:
    text = " ".join(str(value or "").split()).strip()
    if not text:
        return ""
    if len(text) > MAX_PREDICTED_ANSWER_CHARS:
        text = f"{text[: MAX_PREDICTED_ANSWER_CHARS - 1].rstrip()}..."
    if "가능성이" in text or "것 같습니다" in text or "추정" in text:
        return text
    return f"{text} 라고 답할 가능성이 높습니다."


def _normalize_evaluation_guide(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return "상: 실제 사례와 본인 역할, 결과를 구체적으로 설명함\n중: 사례는 있으나 역할 또는 결과 설명이 일부 모호함\n하: 일반론만 말하고 실제 사례나 결과가 없음"

    lines = [line.strip(" -\t") for line in text.splitlines() if line.strip()]
    labeled = {"상": "", "중": "", "하": ""}
    for line in lines:
        for key in labeled:
            if line.startswith(f"{key}:"):
                labeled[key] = line.split(":", 1)[1].strip()

    if all(labeled.values()):
        return "\n".join(f"{key}: {value}" for key, value in labeled.items())

    parts = [segment.strip() for segment in text.replace("\n", " ").split(".") if segment.strip()]
    fallback = parts[:3]
    while len(fallback) < 3:
        fallback.append("핵심 근거와 구체성이 더 필요함")
    return "\n".join(
        [
            f"상: {fallback[0]}",
            f"중: {fallback[1]}",
            f"하: {fallback[2]}",
        ]
    )


def _build_retry_guidance(question: QuestionSet) -> str:
    guidance = " ".join(
        part.strip()
        for part in [
            str(question.get("review_reason") or "").strip(),
            str(question.get("recommended_revision") or "").strip(),
            str(question.get("retry_guidance") or "").strip(),
        ]
        if part and str(part).strip()
    ).strip()
    return guidance[:280]


def _canonical_retry_guidance(
    issue_types: list[str],
    requested_fields: list[str],
    question: QuestionSet,
) -> str:
    issue_set = set(issue_types)
    field_set = set(requested_fields)
    parts: list[str] = []

    if "predicted_answer" in field_set or "over_specific_predicted_answer" in issue_set:
        parts.append(
            "predicted_answer는 문서에 직접 있는 사실만 바탕으로 더 짧고 약한 추정형 표현으로 수정하세요."
        )
    if "follow_up_question" in field_set and "weak_evidence" in issue_set:
        parts.append(
            "follow_up_question은 수치, 기간, 실제 행동, 결과 중 가장 부족한 한 가지를 구체적으로 확인하도록 수정하세요."
        )
    if "question_text" in field_set and "weak_evidence" in issue_set:
        parts.append(
            "question_text는 문서에 직접 근거가 있는 검증 포인트만 남기고, 문서에 없는 기술스택이나 성과는 새로 요구하지 마세요."
        )
    if "evaluation_guide" in field_set or "weak_evaluation_guide" in issue_set:
        parts.append(
            "evaluation_guide는 상/중/하 3줄 체크형을 유지하고, 무엇을 들으면 점수를 줄지 짧게 적으세요."
        )
    if not parts and "weak_evidence" in issue_set:
        parts.append(
            "문서에서 확인 가능한 근거만 바탕으로, 실제 행동과 결과를 더 직접 검증하는 방향으로 수정하세요."
        )

    guidance = " ".join(parts).strip()
    if "Slack" in guidance and "Slack" not in str(question.get("question_text") or ""):
        guidance = guidance.replace("Slack", "협업 도구")
    return guidance[:280]


def _infer_requested_revision_fields(
    issue_types: list[str],
    existing_fields: list[str],
) -> list[str]:
    if existing_fields:
        return existing_fields

    field_order = [
        "question_text",
        "generation_basis",
        "evaluation_guide",
        "predicted_answer",
        "follow_up_question",
        "document_evidence",
    ]
    mapped: list[str] = []
    issue_map = {
        "job_relevance_issue": ["question_text", "generation_basis"],
        "weak_evidence": ["generation_basis", "document_evidence"],
        "duplicate_question": ["question_text"],
        "too_generic": ["question_text"],
        "fairness_risk": ["question_text", "evaluation_guide"],
        "too_long_for_interview": ["question_text", "follow_up_question", "evaluation_guide"],
        "difficulty_mismatch": ["question_text", "evaluation_guide"],
        "weak_evaluation_guide": ["evaluation_guide"],
        "over_specific_predicted_answer": ["predicted_answer", "follow_up_question"],
    }
    for issue_type in issue_types:
        for field_name in issue_map.get(issue_type, []):
            if field_name not in mapped:
                mapped.append(field_name)
    return sorted(mapped, key=field_order.index) if mapped else ["question_text", "evaluation_guide"]


def _recruitment_criteria(state: AgentState) -> str:
    """프롬프트 프로필 안의 채용 기준을 꺼낸다."""
    prompt_profile = state.get("prompt_profile") or {}
    return str(
        prompt_profile.get("system_prompt")
        or "채용 기준이 별도로 제공되지 않았습니다."
    )


def _difficulty_bucket(state: AgentState) -> str:
    """난이도 문자열을 내부 분기용 버킷으로 단순화한다."""
    raw = str(state.get("difficulty_level") or "").strip().upper()
    if raw in {"JUNIOR", "INTERN", "NEW_GRAD", "ENTRY"}:
        return "JUNIOR"
    if raw in {"MID", "SENIOR", "LEAD", "STAFF", "PRINCIPAL"}:
        return "EXPERIENCED"
    return "GENERAL"


def _difficulty_guidance(state: AgentState) -> str:
    """Questioner/Predictor/Driller가 공통으로 참고할 난이도 해석 문장."""
    bucket = _difficulty_bucket(state)
    if bucket == "JUNIOR":
        return (
            "이 지원자는 신입 또는 주니어 레벨로 본다. "
            "학습 능력, 프로젝트 수행 방식, 문제 해결 접근, 협업 태도, 기본기를 중심으로 질문하라. "
            "문서 근거 없이 운영 오너십, 조직 단위 의사결정, 리딩 경험을 전제로 질문하면 안 된다."
        )
    if bucket == "EXPERIENCED":
        return (
            "이 지원자는 경력직으로 본다. "
            "실제 업무 경험, 역할 범위, 기여도, 의사결정, 성과 지표, 트레이드오프, 리스크 대응을 중심으로 질문하라. "
            "문서에 구체 경험이 있는데도 너무 일반적인 동기 질문만 반복하면 안 된다."
        )
    return (
        "난이도가 명확하지 않다. 문서가 허용하는 범위 안에서 기본 역량 검증과 경험 검증의 균형을 맞춰라."
    )


def _merge_document_text(state: AgentState) -> str:
    """여러 문서를 하나의 공통 문맥 문자열로 합친다.

    이번 버전에서는 prepare_context를 크게 바꾸지 않기로 했기 때문에,
    문서 요약 노드를 따로 두지 않고 최소한의 병합만 수행한다.
    다만 긴 문서가 있을 때 앞 문서만 과도하게 반영되는 문제를 줄이기 위해
    문서별 예산을 나눠서 잘라 넣는다.
    """
    sections = [
        "[세션]",
        f"session_id: {state.get('session_id')}",
        f"target_job: {state.get('target_job')}",
        f"difficulty_level: {state.get('difficulty_level')}",
        "",
        "[지원자]",
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
                f"[문서 #{document.get('document_id')}]",
                f"type: {document.get('document_type')}",
                f"title: {document.get('title')}",
                clipped or "(추출 텍스트 없음)",
            ]
        )

    merged = "\n".join(sections)
    return merged[:MAX_DOCUMENT_CHARS]


def _format_questions(items: list[QuestionSet], *, include_answer: bool = False) -> str:
    """질문 리스트를 프롬프트 주입용 JSON 텍스트로 바꾼다."""
    if not items:
        return "(없음)"
    compact: list[dict[str, Any]] = []
    for item in items:
        data: dict[str, Any] = {
            "id": item.get("id"),
            "category": item.get("category"),
            "question_text": item.get("question_text"),
            "generation_basis": item.get("generation_basis"),
            "document_evidence": _normalize_document_evidence(item.get("document_evidence", [])),
            "evaluation_guide": item.get("evaluation_guide"),
            "risk_tags": item.get("risk_tags", []),
            "competency_tags": item.get("competency_tags", []),
            "status": item.get("status"),
            "reject_reason": item.get("reject_reason") or item.get("recommended_revision"),
            "requested_revision_fields": item.get("requested_revision_fields", []),
            "review_issue_types": item.get("review_issue_types", []),
            "regen_targets": item.get("regen_targets", []),
            "retry_guidance": item.get("retry_guidance", ""),
        }
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
    return _json(compact)


def _question_id(question: QuestionSet, index: int) -> str:
    """질문 id가 비어 있으면 안전한 fallback id를 만든다."""
    return str(question.get("id") or f"q-{index + 1}")


def _allocate_question_id(used_ids: set[str], counter: list[int]) -> str:
    """새 질문을 append할 때 기존 질문과 겹치지 않는 id를 발급한다."""
    while True:
        counter[0] += 1
        candidate = f"q-{counter[0]}"
        if candidate not in used_ids:
            used_ids.add(candidate)
            return candidate


def _ensure_question_ids(questions: list[QuestionSet]) -> None:
    """질문 리스트 안의 모든 질문이 안정적인 id를 갖도록 보장한다."""
    used_ids: set[str] = set()
    max_seen = 0
    for question in questions:
        question_id = str(question.get("id") or "")
        if not question_id:
            continue
        used_ids.add(question_id)
        if question_id.startswith("q-"):
            try:
                max_seen = max(max_seen, int(question_id.removeprefix("q-")))
            except ValueError:
                continue

    counter = [max_seen]
    for question in questions:
        if not question.get("id"):
            question["id"] = _allocate_question_id(used_ids, counter)


def _default_regen_targets(question: QuestionSet) -> list[str]:
    """부분 수정 대상 필드가 비어 있으면 기본 수정 필드를 정한다."""
    requested = [str(item) for item in question.get("regen_targets") or [] if str(item).strip()]
    if requested:
        return requested
    requested = [
        str(item)
        for item in question.get("requested_revision_fields") or []
        if str(item).strip()
    ]
    return requested or ["question_text", "evaluation_guide"]


def _should_refresh_predicted_answer(question: QuestionSet) -> bool:
    targets = set(_default_regen_targets(question))
    if not question.get("predicted_answer"):
        return True
    return bool(
        {
            "question_text",
            "generation_basis",
            "document_evidence",
            "predicted_answer",
        }
        & targets
    )


def _should_refresh_follow_up(question: QuestionSet) -> bool:
    targets = set(_default_regen_targets(question))
    if not question.get("follow_up_question"):
        return True
    return bool({"question_text", "predicted_answer", "follow_up_question"} & targets)


def _calculate_average(scores: dict[str, int], expected_keys: list[str]) -> float:
    """루브릭 점수 dict에서 평균을 계산한다."""
    values = [max(1, min(5, int(scores[key]))) for key in expected_keys if key in scores]
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def _score_reason(question_scores: dict[str, int], guide_scores: dict[str, int]) -> str:
    """평균 점수 문자열을 남겨서 디버깅과 로그 확인을 쉽게 한다."""
    q_avg = _calculate_average(question_scores, QUESTION_QUALITY_KEYS)
    g_avg = _calculate_average(guide_scores, EVALUATION_GUIDE_KEYS)
    return f"question_quality_avg={q_avg}, evaluation_guide_avg={g_avg}"


async def prepare_context_node(state: AgentState) -> dict[str, Any]:
    """문서/질문 공통 문맥을 준비하는 첫 노드."""
    questions = list(state.get("questions") or [])
    _ensure_question_ids(questions)

    update: dict[str, Any] = {"questions": questions}
    if not state.get("candidate_context"):
        update["candidate_context"] = _merge_document_text(state)
    return update


def _questioner_mode(state: AgentState, questions: list[QuestionSet]) -> tuple[str, list[QuestionSet]]:
    """현재 요청이 신규 생성인지, 추가 생성인지, 부분 수정인지 판단한다."""
    rewrite_targets = [
        item
        for item in questions
        if item.get("status") in {"rejected", "needs_revision"}
    ]
    if rewrite_targets:
        has_partial = any(_default_regen_targets(item) for item in rewrite_targets)
        return ("partial_rewrite" if has_partial else "rewrite"), rewrite_targets

    human_action = (state.get("human_action") or "").strip()
    target_ids = {str(qid) for qid in (state.get("target_question_ids") or [])}
    if human_action in {"regenerate", "regenerate_question"} and target_ids:
        targets = [
            item for item in questions if str(item.get("id") or "") in target_ids
        ]
        has_partial = any(_default_regen_targets(item) for item in targets)
        return ("partial_rewrite" if has_partial else "rewrite"), targets
    if human_action in {"more", "more_questions"}:
        return "more", []
    if human_action in {"add_question", "generate_follow_up", "risk_questions", "different_perspective"}:
        return "add_question", []
    return "initial", []


def _task_instruction(mode: str, targets: list[QuestionSet]) -> str:
    """Questioner에게 줄 핵심 작업 지시문을 만든다."""
    if mode == "initial":
        return (
            f"새 면접 질문 {DEFAULT_QUESTION_COUNT}개를 생성하라. "
            f"모든 question_text는 {MAX_QUESTION_TEXT_CHARS}자 이내로 유지하고 실제 면접에서 바로 읽을 수 있게 작성하라."
        )
    if mode == "more":
        return (
            f"기존 질문과 중복되지 않는 추가 질문 {MORE_QUESTION_COUNT}개를 생성하라. "
            f"모든 question_text는 {MAX_QUESTION_TEXT_CHARS}자 이내로 유지하라."
        )
    if mode == "add_question":
        return (
            f"추가 지시사항을 반영한 질문 {ADD_QUESTION_COUNT}개를 생성하라. "
            f"모든 question_text는 {MAX_QUESTION_TEXT_CHARS}자 이내로 유지하라."
        )

    target_block = _format_questions(targets, include_answer=True)
    revision_rules = (
        "수정 시 review_issue_types, requested_revision_fields, retry_guidance를 우선 반영하라. "
        "predicted_answer는 사실 단정형이 아니라 짧은 추정형으로 유지하고, "
        "follow_up_question은 가장 중요한 검증 포인트 1개만 묻는 1문장으로 작성하라. "
        "evaluation_guide는 반드시 상/중/하 3줄 체크형으로 작성하라."
    )
    return (
        "지정된 질문만 수정하고, 나머지 질문은 유지하라. "
        "requested_revision_fields 또는 regen_targets가 있으면 해당 필드만 우선 수정하고, "
        "일관성을 위해 꼭 필요하지 않다면 나머지 필드는 건드리지 마라. "
        f"{revision_rules}\n"
        f"{target_block}"
    )


def _build_question_entry(
    model: dict[str, Any],
    *,
    question_id: str,
    generation_mode: str,
    existing: QuestionSet | None = None,
    requested_fields: list[str] | None = None,
) -> QuestionSet:
    """LLM 응답을 내부 QuestionSet 형태로 맞춘다.

    신규 생성과 재작성 모두 이 함수를 거치기 때문에,
    질문 기본값과 초기 상태를 한 곳에서 통일할 수 있다.
    """
    question_text = _clip_question_text(model.get("question_text") or "")
    entry: QuestionSet = {
        "id": question_id,
        "category": model.get("category") or (existing or {}).get("category") or "OTHER",
        "generation_basis": model.get("generation_basis")
        or (existing or {}).get("generation_basis")
        or "",
        "document_evidence": _normalize_document_evidence(
            model.get("document_evidence")
            or list((existing or {}).get("document_evidence") or [])
        ),
        "question_text": question_text or (existing or {}).get("question_text") or "",
        "evaluation_guide": _normalize_evaluation_guide(
            model.get("evaluation_guide")
            or (existing or {}).get("evaluation_guide")
            or ""
        ),
        "predicted_answer": "",
        "predicted_answer_basis": "",
        "answer_confidence": "",
        "answer_risk_points": [],
        "follow_up_question": "",
        "follow_up_basis": "",
        "drill_type": "",
        "risk_tags": model.get("risk_tags") or list((existing or {}).get("risk_tags") or []),
        "competency_tags": model.get("competency_tags")
        or list((existing or {}).get("competency_tags") or []),
        "review_status": "needs_revision",
        "review_reason": "",
        "reject_reason": "",
        "recommended_revision": "",
        "review_issue_types": [],
        "requested_revision_fields": list(requested_fields or []),
        "question_quality_scores": {},
        "evaluation_guide_scores": {},
        "question_quality_average": 0.0,
        "evaluation_guide_average": 0.0,
        "score": 0.0,
        "score_reason": "",
        "status": "pending",
        "regen_targets": list(requested_fields or []),
        "generation_mode": generation_mode,
        "retry_guidance": str((existing or {}).get("retry_guidance") or ""),
    }
    return entry


async def questioner_node(state: AgentState) -> dict[str, Any]:
    """질문 생성 또는 질문 수정 담당 노드."""
    questions = list(state.get("questions") or [])
    _ensure_question_ids(questions)
    mode, targets = _questioner_mode(state, questions)

    update: dict[str, Any] = {
        "human_action": None,
        "additional_instruction": None,
        "target_question_ids": [],
        "generation_mode": mode,
    }
    if mode in {"rewrite", "partial_rewrite"}:
        update["retry_count"] = state.get("retry_count", 0) + 1

    user_prompt = prompts.QUESTIONER_USER_PROMPT.format(
        target_job=state.get("target_job") or "(미지정)",
        difficulty_level=state.get("difficulty_level") or "(미지정)",
        difficulty_guidance=_difficulty_guidance(state),
        recruitment_criteria=_recruitment_criteria(state),
        candidate_context=state.get("candidate_context") or "",
        mode=mode,
        additional_instruction=state.get("additional_instruction") or "(없음)",
        existing_questions=_format_questions(questions, include_answer=True),
        retry_feedback=_format_questions(targets, include_answer=True),
        task_instruction=_task_instruction(mode, targets),
        question_text_limit=MAX_QUESTION_TEXT_CHARS,
    )

    new_usages: list[dict[str, Any]] = []
    new_warnings: list[dict[str, Any]] = []
    try:
        parsed, usages = await call_structured_output_with_usage(
            node_name="questioner",
            system_prompt=prompts.QUESTIONER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=QuestionerOutput,
        )
        new_usages.extend(usages)
    except StructuredOutputCallError as exc:
        new_usages.extend(exc.usages)
        new_warnings.append({"node": "questioner", "message": str(exc)})
        update["questions"] = questions
        update["llm_usages"] = list(state.get("llm_usages") or []) + new_usages
        update["node_warnings"] = list(state.get("node_warnings") or []) + new_warnings
        return update

    by_id = {str(item["id"]): item for item in questions if item.get("id")}
    should_append = mode in {"initial", "more", "add_question"}

    used_ids: set[str] = set(by_id.keys())
    max_seen = 0
    for existing_id in used_ids:
        if existing_id.startswith("q-"):
            try:
                max_seen = max(max_seen, int(existing_id.removeprefix("q-")))
            except ValueError:
                continue
    id_counter = [max_seen]

    target_ids = [str(item.get("id") or "") for item in targets]
    target_regen_map = {str(item.get("id") or ""): _default_regen_targets(item) for item in targets}

    for index, question in enumerate(parsed.questions):
        model = question.model_dump(mode="json")
        if should_append:
            question_id = _allocate_question_id(used_ids, id_counter)
            entry = _build_question_entry(
                model,
                question_id=question_id,
                generation_mode=mode,
            )
            questions.append(entry)
            by_id[question_id] = entry
            continue

        llm_id = str(model.get("id") or "")
        fallback_id = target_ids[index] if index < len(target_ids) else ""
        question_id = llm_id if llm_id in by_id else fallback_id
        if not question_id or question_id not in by_id:
            new_warnings.append(
                {
                    "node": "questioner",
                    "message": f"재작성 응답을 기존 질문 id와 매칭하지 못했습니다. (llm_id={llm_id or '없음'})",
                }
            )
            continue

        existing = by_id[question_id]
        requested_fields = target_regen_map.get(question_id, [])
        patched = _build_question_entry(
            model,
            question_id=question_id,
            generation_mode=mode,
            existing=existing,
            requested_fields=requested_fields,
        )

        if mode == "partial_rewrite" and requested_fields:
            patch_fields = set(requested_fields)
            for field_name in ("question_text", "evaluation_guide", "generation_basis"):
                if field_name not in patch_fields:
                    patched[field_name] = existing.get(field_name, patched[field_name])
            if "document_evidence" not in patch_fields:
                patched["document_evidence"] = list(existing.get("document_evidence") or [])
            if "category" not in patch_fields:
                patched["category"] = existing.get("category", patched["category"])
            if "predicted_answer" not in patch_fields:
                patched["predicted_answer"] = existing.get("predicted_answer", "")
                patched["predicted_answer_basis"] = existing.get("predicted_answer_basis", "")
                patched["answer_confidence"] = existing.get("answer_confidence", "")
                patched["answer_risk_points"] = list(existing.get("answer_risk_points") or [])
            if "follow_up_question" not in patch_fields:
                patched["follow_up_question"] = existing.get("follow_up_question", "")
                patched["follow_up_basis"] = existing.get("follow_up_basis", "")
                patched["drill_type"] = existing.get("drill_type", "")
        else:
            patched["regen_targets"] = []
            patched["requested_revision_fields"] = []

        existing.update(patched)

    update["questions"] = questions
    if new_usages:
        update["llm_usages"] = list(state.get("llm_usages") or []) + new_usages
    if new_warnings:
        update["node_warnings"] = list(state.get("node_warnings") or []) + new_warnings
    return update


async def predictor_node(state: AgentState) -> dict[str, Any]:
    """질문별 예상 답변과 불확실성 신호를 생성한다."""
    questions = list(state.get("questions") or [])
    targets = [
        item
        for item in questions
        if item.get("status") in {"pending", "human_rejected", "needs_revision"}
        and _should_refresh_predicted_answer(item)
    ]
    if not targets:
        return {}

    user_prompt = prompts.PREDICTOR_USER_PROMPT.format(
        target_job=state.get("target_job") or "(미지정)",
        difficulty_level=state.get("difficulty_level") or "(미지정)",
        difficulty_guidance=_difficulty_guidance(state),
        candidate_context=_clip(state.get("candidate_context") or "", PREDICTOR_DOCUMENT_CHARS),
        questions=_format_questions(targets),
        retry_feedback=_format_questions(targets, include_answer=True),
    )
    new_usages: list[dict[str, Any]] = []
    new_warnings: list[dict[str, Any]] = []
    try:
        parsed, usages = await call_structured_output_with_usage(
            node_name="predictor",
            system_prompt=prompts.PREDICTOR_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=PredictorOutput,
        )
        new_usages.extend(usages)
    except StructuredOutputCallError as exc:
        new_usages.extend(exc.usages)
        new_warnings.append({"node": "predictor", "message": str(exc)})
        return {
            "llm_usages": list(state.get("llm_usages") or []) + new_usages,
            "node_warnings": list(state.get("node_warnings") or []) + new_warnings,
        }

    by_id = {str(item["id"]): item for item in questions if item.get("id")}
    for answer in parsed.answers:
        model = answer.model_dump(mode="json")
        target = by_id.get(str(model.get("question_id")))
        if target is None:
            continue
        target["predicted_answer"] = _normalize_predicted_answer(
            model.get("predicted_answer") or ""
        )
        target["predicted_answer_basis"] = model.get("predicted_answer_basis") or ""
        target["answer_confidence"] = model.get("answer_confidence") or ""
        target["answer_risk_points"] = list(model.get("answer_risk_points") or [])

    update: dict[str, Any] = {"questions": questions}
    if new_usages:
        update["llm_usages"] = list(state.get("llm_usages") or []) + new_usages
    if new_warnings:
        update["node_warnings"] = list(state.get("node_warnings") or []) + new_warnings
    return update


async def driller_node(state: AgentState) -> dict[str, Any]:
    """예상 답변을 바탕으로 검증용 꼬리질문을 만든다."""
    questions = list(state.get("questions") or [])
    targets = [
        item
        for item in questions
        if item.get("status") in {"pending", "human_rejected", "needs_revision"}
        and item.get("predicted_answer")
        and _should_refresh_follow_up(item)
    ]
    if not targets:
        return {}

    user_prompt = prompts.DRILLER_USER_PROMPT.format(
        target_job=state.get("target_job") or "(미지정)",
        difficulty_level=state.get("difficulty_level") or "(미지정)",
        difficulty_guidance=_difficulty_guidance(state),
        recruitment_criteria=_recruitment_criteria(state),
        questions=_format_questions(targets, include_answer=True),
        retry_feedback=_format_questions(targets, include_answer=True),
    )
    new_usages: list[dict[str, Any]] = []
    new_warnings: list[dict[str, Any]] = []
    try:
        parsed, usages = await call_structured_output_with_usage(
            node_name="driller",
            system_prompt=prompts.DRILLER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=DrillerOutput,
        )
        new_usages.extend(usages)
    except StructuredOutputCallError as exc:
        new_usages.extend(exc.usages)
        new_warnings.append({"node": "driller", "message": str(exc)})
        return {
            "llm_usages": list(state.get("llm_usages") or []) + new_usages,
            "node_warnings": list(state.get("node_warnings") or []) + new_warnings,
        }

    by_id = {str(item["id"]): item for item in questions if item.get("id")}
    for follow_up in parsed.follow_ups:
        model = follow_up.model_dump(mode="json")
        target = by_id.get(str(model.get("question_id")))
        if target is None:
            continue
        target["follow_up_question"] = _clip_follow_up_text(
            model.get("follow_up_question") or ""
        )
        target["follow_up_basis"] = model.get("follow_up_basis") or ""
        target["drill_type"] = model.get("drill_type") or ""

    update: dict[str, Any] = {"questions": questions}
    if new_usages:
        update["llm_usages"] = list(state.get("llm_usages") or []) + new_usages
    if new_warnings:
        update["node_warnings"] = list(state.get("node_warnings") or []) + new_warnings
    return update


def _fallback_answer(question_id: str) -> PredictedAnswer:
    """예상 답변 생성이 실패했을 때 사용하는 기본값."""
    return PredictedAnswer(
        question_id=question_id,
        predicted_answer="예상 답변을 생성하지 못했습니다.",
        predicted_answer_basis="Predictor 결과가 없어 기본 문구를 사용했습니다.",
        answer_confidence="low",
        answer_risk_points=["예상답변_누락"],
    )


def _fallback_follow_up(question_id: str) -> FollowUpQuestion:
    """꼬리질문 생성이 실패했을 때 사용하는 기본값."""
    return FollowUpQuestion(
        question_id=question_id,
        follow_up_question="방금 말씀하신 경험에서 본인의 역할과 실제 기여를 조금 더 구체적으로 설명해 주실 수 있을까요?",
        follow_up_basis="Driller 결과가 없어 기본 검증형 꼬리질문을 사용했습니다.",
        drill_type="OTHER",
    )


def _fallback_review(question_id: str) -> ReviewResult:
    """검토 결과가 비어 있을 때 최소한의 fallback 리뷰를 만든다."""
    return ReviewResult(
        question_id=question_id,
        status="needs_revision",
        reason="Reviewer 결과가 없어 수동 검토가 필요합니다.",
        reject_reason="",
        recommended_revision="직무 관련성, 문서 근거성, 면접 사용성을 다시 확인하세요.",
        question_quality_scores=QuestionQualityRubric.model_validate({}),
        evaluation_guide_scores=EvaluationGuideRubric.model_validate({}),
    )


def _overall_status_from_score(overall_score: float, issue_types: list[str]) -> str:
    """루브릭 평균과 치명 이슈를 함께 보고 최종 상태를 정한다."""
    critical_issue_types = {"fairness_risk", "job_relevance_issue", "weak_evidence"}
    if overall_score >= 4.2 and not (critical_issue_types & set(issue_types)):
        return "approved"
    if overall_score >= 3.0:
        return "needs_revision"
    return "rejected"


async def reviewer_node(state: AgentState) -> dict[str, Any]:
    """질문 세트를 루브릭으로 검토하고 재수정 여부를 결정한다."""
    questions = list(state.get("questions") or [])
    targets = [
        item
        for item in questions
        if item.get("status") in {"pending", "human_rejected", "needs_revision", "rejected"}
    ]
    if not targets:
        return {
            "is_all_approved": bool(questions)
            and all(item.get("status") == "approved" for item in questions)
        }

    user_prompt = prompts.REVIEWER_USER_PROMPT.format(
        target_job=state.get("target_job") or "(미지정)",
        difficulty_level=state.get("difficulty_level") or "(미지정)",
        difficulty_guidance=_difficulty_guidance(state),
        recruitment_criteria=_recruitment_criteria(state),
        questions=_format_questions(targets, include_answer=True),
    )
    new_usages: list[dict[str, Any]] = []
    new_warnings: list[dict[str, Any]] = []
    try:
        parsed, usages = await call_structured_output_with_usage(
            node_name="reviewer",
            system_prompt=prompts.REVIEWER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=ReviewerOutput,
        )
        new_usages.extend(usages)
    except StructuredOutputCallError as exc:
        new_usages.extend(exc.usages)
        new_warnings.append({"node": "reviewer", "message": str(exc)})
        for item in targets:
            item["status"] = "needs_revision"
            item["review_status"] = "needs_revision"
            item["review_reason"] = "Reviewer 호출이 실패해 질문을 다시 검토해야 합니다."
            item["reject_reason"] = "Reviewer 호출 실패"
            item["recommended_revision"] = "프롬프트 형식과 입력 길이를 확인한 뒤 다시 검토하세요."
            item["requested_revision_fields"] = ["question_text", "evaluation_guide"]
            item["review_issue_types"] = ["review_execution_failure"]
        return {
            "questions": questions,
            "retry_count": state.get("max_retry_count", 3),
            "is_all_approved": False,
            "llm_usages": list(state.get("llm_usages") or []) + new_usages,
            "node_warnings": list(state.get("node_warnings") or []) + new_warnings,
        }

    by_id = {str(item["id"]): item for item in questions if item.get("id")}
    for review in parsed.reviews:
        model = review.model_dump(mode="json")
        target = by_id.get(str(model.get("question_id")))
        if target is None:
            continue

        question_scores = {
            key: int(value)
            for key, value in dict(model.get("question_quality_scores") or {}).items()
        }
        guide_scores = {
            key: int(value)
            for key, value in dict(model.get("evaluation_guide_scores") or {}).items()
        }
        question_avg = model.get("question_quality_average") or _calculate_average(
            question_scores,
            QUESTION_QUALITY_KEYS,
        )
        guide_avg = model.get("evaluation_guide_average") or _calculate_average(
            guide_scores,
            EVALUATION_GUIDE_KEYS,
        )
        overall_score = model.get("overall_score") or round((question_avg + guide_avg) / 2, 2)
        issue_types = [str(item) for item in model.get("issue_types") or []]
        status = str(model.get("status") or _overall_status_from_score(overall_score, issue_types))

        target["review_status"] = status
        target["review_reason"] = model.get("reason") or ""
        target["reject_reason"] = model.get("reject_reason") or ""
        target["recommended_revision"] = model.get("recommended_revision") or ""
        target["review_issue_types"] = issue_types
        target["requested_revision_fields"] = _infer_requested_revision_fields(
            issue_types,
            [str(item) for item in model.get("requested_revision_fields") or []],
        )
        target["retry_guidance"] = _canonical_retry_guidance(
            issue_types,
            target["requested_revision_fields"],
            target,
        )
        target["question_quality_scores"] = question_scores
        target["evaluation_guide_scores"] = guide_scores
        target["question_quality_average"] = float(question_avg)
        target["evaluation_guide_average"] = float(guide_avg)
        target["score"] = float(overall_score)
        target["score_reason"] = target["review_reason"] or _score_reason(question_scores, guide_scores)
        target["status"] = status

        if status == "needs_revision" and not target["requested_revision_fields"]:
            target["requested_revision_fields"] = ["question_text", "evaluation_guide"]
        if status != "approved":
            target["regen_targets"] = list(target.get("requested_revision_fields") or [])
        else:
            target["regen_targets"] = []
            target["requested_revision_fields"] = []
            target["retry_guidance"] = ""

    update: dict[str, Any] = {
        "questions": questions,
        "is_all_approved": bool(questions)
        and all(item.get("status") == "approved" for item in questions),
    }
    if new_usages:
        update["llm_usages"] = list(state.get("llm_usages") or []) + new_usages
    if new_warnings:
        update["node_warnings"] = list(state.get("node_warnings") or []) + new_warnings
    return update


def review_router(state: AgentState) -> str:
    """Reviewer 결과를 보고 Questioner로 되돌릴지 종료할지 결정한다."""
    retryable_statuses = {"needs_revision", "rejected"}
    has_retryable = any(
        item.get("status") in retryable_statuses for item in state.get("questions", [])
    )
    if has_retryable and state.get("retry_count", 0) < state.get("max_retry_count", 3):
        return "retry"
    return "end"


def _analysis_summary(state: AgentState) -> DocumentAnalysisOutput:
    """최종 응답용 간단한 분석 요약을 만든다."""
    questions = state.get("questions", [])
    risk_tags = sorted(
        {
            tag
            for item in questions
            for tag in item.get("risk_tags", [])
            if tag
        }
    )
    return DocumentAnalysisOutput(
        strengths=[],
        weaknesses=[],
        risks=risk_tags[:8],
        document_evidence=[],
        job_fit=(
            "그래프는 별도 Analyzer 노드 없이 질문 생성 근거와 Reviewer 결과를 바탕으로 직무 적합성 신호를 정리합니다."
        ),
        questionable_points=[
            item.get("generation_basis", "")
            for item in questions[:5]
            if item.get("generation_basis")
        ],
    )


def _requested_question_count(state: AgentState) -> int:
    """현재 모드에서 몇 개 질문이 있어야 정상 완료인지 계산한다."""
    mode = state.get("generation_mode")
    if mode == "more":
        return MORE_QUESTION_COUNT
    if mode == "add_question":
        return ADD_QUESTION_COUNT
    return DEFAULT_QUESTION_COUNT


def build_response(state: AgentState) -> QuestionGenerationResponse:
    """그래프 내부 state를 최종 응답 스키마로 변환한다.

    중요한 원칙은 '노드가 만든 결과를 최대한 그대로 보존한다'는 것이다.
    즉 예쁘게 덮어쓰기보다는, 실제 생성된 메타데이터를 응답에 싣는 데 초점을 둔다.
    """
    items: list[InterviewQuestionItem] = []
    for index, question in enumerate(state.get("questions", [])):
        question_id = _question_id(question, index)
        question_model = QuestionCandidate.model_validate(
            {
                "id": question_id,
                "category": question.get("category") or "OTHER",
                "question_text": question.get("question_text") or "",
                "generation_basis": question.get("generation_basis") or "",
                "document_evidence": _normalize_document_evidence(
                    question.get("document_evidence") or []
                ),
                "evaluation_guide": _normalize_evaluation_guide(
                    question.get("evaluation_guide") or ""
                ),
                "risk_tags": question.get("risk_tags") or [],
                "competency_tags": question.get("competency_tags") or [],
            }
        )
        answer = PredictedAnswer.model_validate(
            {
                "question_id": question_id,
                "predicted_answer": _normalize_predicted_answer(
                    question.get("predicted_answer")
                    or _fallback_answer(question_id).predicted_answer
                ),
                "predicted_answer_basis": question.get("predicted_answer_basis")
                or _fallback_answer(question_id).predicted_answer_basis,
                "answer_confidence": question.get("answer_confidence")
                or _fallback_answer(question_id).answer_confidence,
                "answer_risk_points": question.get("answer_risk_points")
                or _fallback_answer(question_id).answer_risk_points,
            }
        )
        follow_up = FollowUpQuestion.model_validate(
            {
                "question_id": question_id,
                "follow_up_question": _clip_follow_up_text(
                    question.get("follow_up_question")
                    or _fallback_follow_up(question_id).follow_up_question
                ),
                "follow_up_basis": question.get("follow_up_basis")
                or _fallback_follow_up(question_id).follow_up_basis,
                "drill_type": question.get("drill_type")
                or _fallback_follow_up(question_id).drill_type,
            }
        )
        review = ReviewResult.model_validate(
            {
                "question_id": question_id,
                "status": question.get("review_status") or "needs_revision",
                "reason": question.get("review_reason") or _fallback_review(question_id).reason,
                "reject_reason": question.get("reject_reason") or "",
                "recommended_revision": question.get("recommended_revision") or "",
                "issue_types": question.get("review_issue_types") or [],
                "requested_revision_fields": question.get("requested_revision_fields") or [],
                "question_quality_scores": question.get("question_quality_scores") or {},
                "evaluation_guide_scores": question.get("evaluation_guide_scores") or {},
                "question_quality_average": question.get("question_quality_average") or 0.0,
                "evaluation_guide_average": question.get("evaluation_guide_average") or 0.0,
                "overall_score": question.get("score") or 0.0,
            }
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
                answer_confidence=answer.answer_confidence,
                answer_risk_points=answer.answer_risk_points,
                follow_up_question=follow_up.follow_up_question,
                follow_up_basis=follow_up.follow_up_basis,
                drill_type=follow_up.drill_type,
                risk_tags=question_model.risk_tags,
                competency_tags=question_model.competency_tags,
                review=review,
                score=float(question.get("score") or 0.0),
                score_reason=question.get("score_reason") or "Reviewer 점수 사유가 비어 있습니다.",
            )
        )

    approved_count = sum(1 for item in items if item.review.status == "approved")
    all_approved = bool(items) and approved_count == len(items)
    hit_retry_limit = state.get("retry_count", 0) >= state.get("max_retry_count", 3)
    generation_mode = state.get("generation_mode") or "initial"
    requested_count = _requested_question_count(state)
    enough_questions = len(items) >= requested_count if generation_mode in {"initial", "more", "add_question"} else bool(items)
    is_partial = not enough_questions or not all_approved or hit_retry_limit

    return QuestionGenerationResponse(
        session_id=state.get("session_id"),
        candidate_id=state.get("candidate_id"),
        target_job=state.get("target_job") or "",
        difficulty_level=state.get("difficulty_level"),
        status="partial_completed" if is_partial else "completed",
        analysis_summary=_analysis_summary(state),
        questions=items,
        generation_metadata={
            "pipeline": "interview_graph",
            "generation_mode": generation_mode,
            "total_candidate_questions": len(state.get("questions", [])),
            "selected_question_count": len(items),
            "requested_question_count": requested_count,
            "retry_count": state.get("retry_count", 0),
            "is_all_approved": all_approved,
            "node_warnings": state.get("node_warnings", []),
            "graph": "PrepareContext -> Questioner -> Predictor -> Driller -> Reviewer",
        },
    )
