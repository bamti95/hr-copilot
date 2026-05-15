"""직무명과 직무 코드를 정규화하는 유틸리티다."""

from __future__ import annotations

import re


JOB_POSITION_CODES = (
    "STRATEGY_PLANNING",
    "HR",
    "MARKETING",
    "AI_DEV_DATA",
    "SALES",
)

JOB_POSITION_LABELS = {
    "STRATEGY_PLANNING": "기획·전략",
    "HR": "인사·HR",
    "MARKETING": "마케팅·광고·MD",
    "AI_DEV_DATA": "AI·개발·데이터",
    "SALES": "영업",
}

JOB_POSITION_ALIASES = {
    "STRATEGY_PLANNING": (
        "strategy",
        "planning",
        "business planning",
        "기획",
        "전략",
        "사업기획",
        "전략기획",
        "경영기획",
    ),
    "HR": (
        "hr",
        "human resources",
        "people",
        "인사",
        "채용",
        "조직문화",
        "평가",
        "보상",
        "노무",
    ),
    "MARKETING": (
        "marketing",
        "md",
        "마케팅",
        "광고",
        "브랜드",
        "콘텐츠",
        "퍼포먼스",
        "상품기획",
    ),
    "AI_DEV_DATA": (
        "ai",
        "data",
        "developer",
        "engineer",
        "software",
        "backend",
        "frontend",
        "ml",
        "개발",
        "데이터",
        "인공지능",
        "머신러닝",
        "백엔드",
        "프론트엔드",
    ),
    "SALES": (
        "sales",
        "영업",
        "세일즈",
        "고객관리",
        "account",
        "business development",
    ),
}

_EXPERIENCE_SUFFIX_RE = re.compile(r"\((신입|경력)\)\s*$")


def extract_experience_suffix(value: str | None) -> str | None:
    if not value:
        return None

    match = _EXPERIENCE_SUFFIX_RE.search(value.strip())
    return match.group(1) if match else None


def strip_experience_suffix(value: str | None) -> str:
    if not value:
        return ""

    return _EXPERIENCE_SUFFIX_RE.sub("", value.strip()).strip()


def normalize_job_position_code(value: str | None) -> str | None:
    normalized = strip_experience_suffix(value)
    if not normalized:
        return None

    upper_value = normalized.upper()
    if upper_value in JOB_POSITION_CODES:
        return upper_value

    compact = re.sub(r"[\s/·+_\-()]+", "", normalized).lower()
    lowered = normalized.lower()

    for code, label in JOB_POSITION_LABELS.items():
        label_compact = re.sub(r"[\s/·+_\-()]+", "", label).lower()
        if compact == label_compact:
            return code

    for code, aliases in JOB_POSITION_ALIASES.items():
        if any(alias.lower() in lowered or alias.lower() in compact for alias in aliases):
            return code

    return None


def normalize_job_position(value: str | None) -> str | None:
    code = normalize_job_position_code(value)
    if not code:
        return None

    suffix = extract_experience_suffix(value)
    return f"{code} ({suffix})" if suffix else code


