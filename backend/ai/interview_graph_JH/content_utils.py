"""Text normalization helpers for the JH interview graph."""

from __future__ import annotations

import json
from typing import Any

from ai.interview_graph_JH.config import (
    MAX_FOLLOW_UP_CHARS,
    MAX_PREDICTED_ANSWER_CHARS,
    MAX_QUESTION_TEXT_CHARS,
)
from ai.interview_graph_JH.state import QuestionSet


def to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def clip_text(value: str, max_chars: int) -> str:
    text = value.strip()
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars]}\n\n...(길이 제한으로 일부 생략)"


def clip_question_text(value: str) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= MAX_QUESTION_TEXT_CHARS:
        return text
    clipped = text[: MAX_QUESTION_TEXT_CHARS - 1].rstrip()
    return f"{clipped}..."


def clip_follow_up_text(value: str) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= MAX_FOLLOW_UP_CHARS:
        return text
    clipped = text[: MAX_FOLLOW_UP_CHARS - 1].rstrip()
    return f"{clipped}..."


def normalize_document_evidence(value: Any) -> list[str]:
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


def _conservative_predicted_answer(evidence: list[str]) -> str:
    if not evidence:
        return "문서 기준으로는 관련 경험을 중심으로 답할 가능성이 있습니다."
    anchor = evidence[0]
    if len(anchor) > 60:
        anchor = f"{anchor[:57].rstrip()}..."
    return f"문서 기준으로는 {anchor} 경험을 중심으로 답할 가능성이 있습니다."


def normalize_predicted_answer(
    value: str,
    *,
    issue_types: list[str] | None = None,
    evidence: list[str] | None = None,
) -> str:
    text = " ".join(str(value or "").split()).strip()
    if not text:
        return ""

    issue_set = set(issue_types or [])
    evidence = list(evidence or [])
    conservative_markers = [
        "직접",
        "성과",
        "개선",
        "구축",
        "도입",
        "전환율",
        "리드",
        "매출",
        "KPI",
    ]

    if "doc_evidence_missing" in issue_set:
        return _conservative_predicted_answer(evidence)

    if len(text) > MAX_PREDICTED_ANSWER_CHARS:
        text = f"{text[: MAX_PREDICTED_ANSWER_CHARS - 1].rstrip()}..."

    if {"over_specific_predicted_answer", "weak_evidence"} & issue_set:
        if len(text) > 95 or any(marker in text for marker in conservative_markers):
            return _conservative_predicted_answer(evidence)

    if any(marker in text for marker in ["가능성", "같습니다", "추정", "보입니다"]):
        return text

    return f"{text} 라고 답할 가능성이 있습니다."


def _has_numeric_evidence(question: QuestionSet) -> bool:
    numeric_source = " ".join(
        [
            " ".join(str(item) for item in question.get("document_evidence") or []),
            str(question.get("generation_basis") or ""),
        ]
    )
    return any(
        marker in numeric_source
        for marker in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "%", "개월", "주", "건", "시간"]
    )


def _soften_exploratory_text(text: str) -> str:
    softened = " ".join(str(text or "").split()).strip()
    replacements = [
        ("몇 %p", "관련 지표 변화"),
        ("몇 %", "관련 지표"),
        ("전후 비교 수치", "기억나는 변화"),
        ("전후 비교", "변화"),
        ("몇 건", "관련 여부"),
        ("몇 일", "일정 변화"),
        ("얼마나 단축", "어떤 변화"),
    ]
    for source, target in replacements:
        softened = softened.replace(source, target)
    return softened


def _pick_follow_up_focus(question: QuestionSet) -> str:
    issue_set = set(
        str(item)
        for item in (
            question.get("retry_issue_types")
            or question.get("review_issue_types")
            or []
        )
    )
    question_text = " ".join(str(question.get("question_text") or "").split())
    guidance = " ".join(
        str(part or "")
        for part in [
            question.get("retry_guidance"),
            question.get("review_reason"),
            question.get("follow_up_question"),
        ]
    )
    has_numeric_evidence = _has_numeric_evidence(question)

    if "doc_evidence_missing" in issue_set:
        if "CRM" in question_text or "KPI" in question_text or "지표" in guidance:
            return "kpi"
        return "action"
    if "기간" in guidance:
        return "period" if has_numeric_evidence else "action"
    if "수치" in guidance or "%" in guidance or "정량" in guidance:
        if not has_numeric_evidence:
            return "result" if ("성과" in guidance or "결과" in guidance) else "action"
        return "metric"
    if "행동" in guidance or "직접" in guidance:
        return "action"
    if "결과" in guidance or "성과" in guidance:
        return "result"
    return "action"


def normalize_follow_up_question(value: str, question: QuestionSet) -> str:
    text = " ".join(str(value or "").split()).strip()
    if not text:
        return ""

    while "(" in text and ")" in text and text.index("(") < text.index(")"):
        start = text.index("(")
        end = text.index(")") + 1
        text = f"{text[:start].rstrip()} {text[end:].lstrip()}".strip()

    issue_set = set(
        str(item)
        for item in (
            question.get("retry_issue_types")
            or question.get("review_issue_types")
            or []
        )
    )
    focus = _pick_follow_up_focus(question)
    has_numeric_evidence = _has_numeric_evidence(question)

    if {"too_long_for_interview", "followup_not_specific", "doc_evidence_missing"} & issue_set:
        if focus == "kpi":
            text = "그 경험에서 중요하게 본 지표가 있었다면 무엇이었고, 기억나는 범위에서 어떻게 봤는지 말씀해 주세요."
        elif focus == "period" and has_numeric_evidence:
            text = "그 경험의 실제 진행 기간만 구체적으로 말씀해 주세요."
        elif focus == "metric" and has_numeric_evidence:
            text = "그 경험과 연결된 핵심 수치 한 가지만 구체적으로 말씀해 주세요."
        elif focus == "result":
            text = "그 경험 이후 실제로 달라진 점이 있었다면, 기억나는 범위에서 한 가지만 말씀해 주세요."
        else:
            text = "그 경험에서 본인이 직접 한 행동 한 가지만 구체적으로 말씀해 주세요."

    if not has_numeric_evidence and any(
        marker in text
        for marker in ["몇 %", "몇 건", "몇 시간", "몇 주", "몇 개월"]
    ):
        if "KPI" in text or "지표" in text:
            text = "그 경험에서 중요하게 본 지표가 있었다면 무엇이었고 그 지표를 어떻게 봤는지 말씀해 주세요."
        else:
            text = "그 경험에서 본인이 직접 한 행동 한 가지와, 가능하면 그 결과도 함께 말씀해 주세요."

    if not has_numeric_evidence:
        softened = _soften_exploratory_text(text)
        if softened != text:
            text = softened
        if any(token in text for token in ["관련 지표", "변화", "일정 변화", "관련 여부"]):
            if all(token not in text for token in ["있었다면", "기억나는 범위", "가능하면"]):
                text = f"{text.rstrip(' .?')} 가능하면 기억나는 범위에서 말씀해 주세요."

    return clip_follow_up_text(text)


def normalize_evaluation_guide(value: str) -> str:
    text = str(value or "").strip()
    labels = ["상", "중", "하"]

    if not text:
        return (
            "상: 실제 본인 행동과 결과를 구체적으로 설명함\n"
            "중: 경험은 있으나 본인 행동이나 결과 설명이 다소 모호함\n"
            "하: 일반론 위주로 말하고 실제 사례와 결과가 부족함"
        )

    lines = [line.strip(" -\t") for line in text.splitlines() if line.strip()]
    labeled: dict[str, str] = {label: "" for label in labels}

    for line in lines:
        for label in labels:
            if line.startswith(f"{label}:"):
                labeled[label] = line.split(":", 1)[1].strip()
                break

    if all(labeled.values()):
        normalized_lines: list[str] = []
        for label in labels:
            content = labeled[label]
            content = (
                content.replace("명확한 수치 제시", "구체한 근거 제시")
                .replace("결과 수치", "결과 근거")
                .replace("정량적 결과", "구체적 결과")
            )
            normalized_lines.append(f"{label}: {content}")
        return "\n".join(normalized_lines)

    parts = [segment.strip() for segment in text.replace("\n", " ").split(".") if segment.strip()]
    fallback = parts[:3]
    while len(fallback) < 3:
        fallback.append("실제 사례와 행동, 결과를 더 구체적으로 설명할 필요가 있음")
    return "\n".join(
        [
            f"상: {fallback[0]}",
            f"중: {fallback[1]}",
            f"하: {fallback[2]}",
        ]
    )
