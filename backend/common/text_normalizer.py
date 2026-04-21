from __future__ import annotations

import logging
import re
import threading
import unicodedata
from collections import Counter
from pathlib import Path

from common.document_types import (
    BOX_DRAWING_PATTERN,
    LINE_NOISE_CHAR_PATTERN,
    LLM_LOW_QUALITY_THRESHOLD,
    LLM_MIN_ACCEPTED_LENGTH_RATIO,
    LLM_MIN_ACCEPTED_MEANINGFUL_RATIO,
    LLM_MIN_SOURCE_CHARS,
    LLM_NORMALIZATION_MODEL,
    LLM_NORMALIZATION_SYSTEM_PROMPT,
    LLM_NORMALIZATION_TIMEOUT_SECONDS,
    LLM_NORMALIZATION_USER_PROMPT_TEMPLATE,
    LLM_OCR_QUALITY_THRESHOLD,
    LLM_PORTFOLIO_QUALITY_THRESHOLD,
    MAX_PAGES_FOR_HEADER_FOOTER_ANALYSIS,
    MAX_REPEATED_LINE_LENGTH,
    MAX_SHORT_NOISE_LINE_LENGTH,
    MEANINGFUL_CHAR_PATTERN,
    PAGE_NUMBER_PATTERN,
    SECTION_HEADING_PATTERN,
)
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_LLM_CLIENT_LOCAL = threading.local()

'''
규칙 기반 정제, 품질 점수, 문서 유형 추론, 조건부 LLM 정제
'''

def normalize_extracted_text(raw_text: str) -> str | None:
    normalized = unicodedata.normalize("NFKC", raw_text or "")
    normalized = normalized.replace("\x00", "")
    normalized = normalized.replace("\u200b", " ")
    normalized = normalized.replace("\ufeff", " ")
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = "\n".join(line.rstrip() for line in normalized.splitlines())
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    normalized = normalized.strip()
    return normalized or None


def normalize_line(line: str) -> str:
    normalized = unicodedata.normalize("NFKC", line)
    normalized = normalized.replace("\u200b", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def looks_like_section_heading(line: str) -> bool:
    normalized = normalize_line(line)
    if not normalized:
        return False
    if len(normalized) > 40:
        return False
    return bool(SECTION_HEADING_PATTERN.match(normalized))


def score_extracted_text(text: str | None) -> int:
    if not text:
        return 0

    normalized = normalize_extracted_text(text)
    if not normalized:
        return 0

    meaningful_chars = len(MEANINGFUL_CHAR_PATTERN.findall(normalized))
    lines = [line for line in normalized.splitlines() if line.strip()]
    long_lines = sum(1 for line in lines if len(line.strip()) >= 12)
    heading_lines = sum(1 for line in lines if looks_like_section_heading(line))
    return meaningful_chars + (len(lines) * 2) + (long_lines * 5) + (heading_lines * 6)


def count_meaningful_chars(text: str | None) -> int:
    if not text:
        return 0
    normalized = normalize_extracted_text(text)
    if not normalized:
        return 0
    return len(MEANINGFUL_CHAR_PATTERN.findall(normalized))


def is_bullet_or_list_line(line: str) -> bool:
    normalized = normalize_line(line)
    return bool(re.match(r"^(?:[-*•▪▫]|[0-9]{1,2}[.)])\s+", normalized))


def is_noise_line(line: str) -> bool:
    normalized = normalize_line(line)
    if not normalized:
        return True
    if PAGE_NUMBER_PATTERN.match(normalized):
        return True
    if BOX_DRAWING_PATTERN.match(normalized):
        return True
    if len(normalized) <= MAX_SHORT_NOISE_LINE_LENGTH and not MEANINGFUL_CHAR_PATTERN.search(normalized):
        return True

    meaningful_chars = len(MEANINGFUL_CHAR_PATTERN.findall(normalized))
    decorative_chars = len(LINE_NOISE_CHAR_PATTERN.findall(normalized))
    if meaningful_chars == 0 and decorative_chars > 0:
        return True
    if meaningful_chars > 0 and decorative_chars >= max(6, meaningful_chars * 2):
        return True
    return False


def deduplicate_text_sections(texts: list[str]) -> str | None:
    unique_sections: list[str] = []
    seen: set[str] = set()

    for text in texts:
        normalized = normalize_extracted_text(text)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique_sections.append(normalized)

    return normalize_extracted_text("\n\n".join(unique_sections))


def collect_repeated_page_edges(page_line_groups: list[list[str]]) -> tuple[set[str], set[str]]:
    header_candidates: Counter[str] = Counter()
    footer_candidates: Counter[str] = Counter()
    page_count = min(len(page_line_groups), MAX_PAGES_FOR_HEADER_FOOTER_ANALYSIS)

    for lines in page_line_groups[:page_count]:
        compact_lines = [line for line in lines if line]
        for line in compact_lines[:2]:
            if len(line) <= MAX_REPEATED_LINE_LENGTH:
                header_candidates[line] += 1
        for line in compact_lines[-2:]:
            if len(line) <= MAX_REPEATED_LINE_LENGTH:
                footer_candidates[line] += 1

    repeat_threshold = 2 if page_count >= 2 else page_count + 1
    repeated_headers = {
        line
        for line, count in header_candidates.items()
        if count >= repeat_threshold and not looks_like_section_heading(line)
    }
    repeated_footers = {
        line
        for line, count in footer_candidates.items()
        if count >= repeat_threshold
    }
    return repeated_headers, repeated_footers


def should_join_lines(previous: str, current: str) -> bool:
    if not previous or not current:
        return False
    if looks_like_section_heading(previous) or looks_like_section_heading(current):
        return False
    if is_bullet_or_list_line(previous) or is_bullet_or_list_line(current):
        return False
    if previous.endswith((".", "!", "?", ":", ";", "]", ")")):
        return False
    if len(previous) <= 3:
        return False
    if re.match(r"^[A-Z][A-Z /&+\-]{2,}$", current):
        return False
    if re.match(r"^[가-힣A-Za-z0-9(]", current):
        return True
    return False


def clean_page_lines(
    raw_lines: list[str],
    *,
    repeated_headers: set[str],
    repeated_footers: set[str],
    ocr_bias: bool,
) -> list[str]:
    cleaned_lines: list[str] = []

    for index, raw_line in enumerate(raw_lines):
        line = normalize_line(raw_line)
        if not line:
            continue
        if line in repeated_headers and index < 3:
            continue
        if line in repeated_footers and index >= max(0, len(raw_lines) - 3):
            continue
        if is_noise_line(line):
            continue

        if ocr_bias:
            line = re.sub(r"([A-Za-z가-힣0-9])\s{2,}([A-Za-z가-힣0-9])", r"\1 \2", line)
            line = re.sub(r"([|/_\-]){2,}", " ", line).strip()
            if is_noise_line(line):
                continue

        cleaned_lines.append(line)

    merged_lines: list[str] = []
    for line in cleaned_lines:
        if not merged_lines:
            merged_lines.append(line)
            continue
        if should_join_lines(merged_lines[-1], line):
            merged_lines[-1] = f"{merged_lines[-1]} {line}".strip()
        else:
            merged_lines.append(line)

    deduped_lines: list[str] = []
    seen_recent: set[str] = set()
    for line in merged_lines:
        if line in seen_recent and len(line) <= MAX_REPEATED_LINE_LENGTH:
            continue
        deduped_lines.append(line)
        if len(line) <= MAX_REPEATED_LINE_LENGTH:
            seen_recent.add(line)

    return deduped_lines


def normalize_document_pages(
    page_snapshots: list,
    *,
    source_type: str,
) -> tuple[str | None, str | None]:
    raw_pages: list[str] = []
    cleaned_pages: list[str] = []
    page_line_groups: list[list[str]] = []

    for snapshot in page_snapshots:
        selected = normalize_extracted_text(snapshot.selected_text or "")
        if not selected:
            continue
        raw_pages.append(selected)
        page_line_groups.append([normalize_line(line) for line in selected.splitlines()])

    if not raw_pages:
        return None, None

    repeated_headers, repeated_footers = collect_repeated_page_edges(page_line_groups)

    for snapshot in page_snapshots:
        selected = normalize_extracted_text(snapshot.selected_text or "")
        if not selected:
            continue
        cleaned_lines = clean_page_lines(
            selected.splitlines(),
            repeated_headers=repeated_headers,
            repeated_footers=repeated_footers,
            ocr_bias=source_type in {"scanned_pdf_ocr", "mixed_pdf"} and snapshot.source_mode == "ocr",
        )
        if cleaned_lines:
            cleaned_pages.append("\n".join(cleaned_lines))

    raw_text = normalize_extracted_text("\n\n".join(raw_pages))
    normalized_text = normalize_extracted_text("\n\n".join(cleaned_pages))
    return raw_text, normalized_text


def infer_document_kind(
    *,
    abs_path: Path,
    normalized_text: str | None,
    source_type: str,
) -> str:
    path_text = abs_path.as_posix().lower()
    text = (normalized_text or "").lower()

    cover_letter_keywords = ["자기소개", "지원동기", "입사 후 포부", "성격의 장단점", "협업 경험"]
    resume_keywords = ["경력", "학력", "기술스택", "자격증", "프로젝트", "career", "experience", "skills"]
    portfolio_keywords = ["portfolio", "포트폴리오", "figma", "prototype", "ux", "ui", "브랜딩", "design system"]

    if "cover_letter" in path_text or any(keyword in text for keyword in cover_letter_keywords):
        return "cover_letter_like"
    if "portfolio" in path_text or any(keyword in text for keyword in portfolio_keywords):
        return "portfolio_layout"
    if "resume" in path_text or "career_description" in path_text or any(keyword in text for keyword in resume_keywords):
        return "resume_like"
    if source_type == "scanned_pdf_ocr":
        return "resume_like"
    return "generic_document"


def collect_quality_metrics(text: str | None) -> dict[str, float]:
    normalized = normalize_extracted_text(text or "")
    if not normalized:
        return {
            "quality_score": 0.0,
            "line_count": 0.0,
            "meaningful_ratio": 0.0,
            "long_line_ratio": 0.0,
            "noisy_line_ratio": 1.0,
            "short_fragment_ratio": 1.0,
            "duplicate_ratio": 1.0,
            "section_bonus": 0.0,
            "meaningful_chars": 0.0,
            "total_chars": 0.0,
        }

    lines = [line for line in normalized.splitlines() if line.strip()]
    if not lines:
        return {
            "quality_score": 0.0,
            "line_count": 0.0,
            "meaningful_ratio": 0.0,
            "long_line_ratio": 0.0,
            "noisy_line_ratio": 1.0,
            "short_fragment_ratio": 1.0,
            "duplicate_ratio": 1.0,
            "section_bonus": 0.0,
            "meaningful_chars": 0.0,
            "total_chars": float(len(normalized)),
        }

    meaningful_chars = len(MEANINGFUL_CHAR_PATTERN.findall(normalized))
    total_chars = max(len(normalized), 1)
    meaningful_ratio = meaningful_chars / total_chars
    long_line_ratio = sum(1 for line in lines if len(line) >= 12) / len(lines)
    noisy_line_ratio = sum(1 for line in lines if is_noise_line(line)) / len(lines)
    short_fragment_ratio = sum(1 for line in lines if len(line) <= 4) / len(lines)
    duplicate_ratio = 1 - (len(set(lines)) / len(lines))
    section_hits = sum(
        1
        for keyword in ("경력", "프로젝트", "기술", "학력", "자격", "자기소개", "지원동기")
        if keyword in normalized
    )
    section_bonus = min(section_hits / 6, 1.0)

    score = (
        (meaningful_ratio * 0.35)
        + (long_line_ratio * 0.2)
        + ((1 - noisy_line_ratio) * 0.15)
        + ((1 - short_fragment_ratio) * 0.1)
        + ((1 - duplicate_ratio) * 0.1)
        + (section_bonus * 0.1)
    )
    return {
        "quality_score": round(max(0.0, min(score, 1.0)), 4),
        "line_count": float(len(lines)),
        "meaningful_ratio": meaningful_ratio,
        "long_line_ratio": long_line_ratio,
        "noisy_line_ratio": noisy_line_ratio,
        "short_fragment_ratio": short_fragment_ratio,
        "duplicate_ratio": duplicate_ratio,
        "section_bonus": section_bonus,
        "meaningful_chars": float(meaningful_chars),
        "total_chars": float(total_chars),
    }


def compute_quality_score(text: str | None) -> float:
    return collect_quality_metrics(text)["quality_score"]


def build_strategy(source_type: str, document_kind: str, quality_score: float) -> str:
    if document_kind == "portfolio_layout":
        base = "portfolio_layout"
    elif source_type == "digital_pdf_text":
        base = "digital_pdf"
    elif source_type == "scanned_pdf_ocr":
        base = "scanned_pdf_ocr"
    elif source_type == "mixed_pdf":
        base = "mixed_pdf_hybrid"
    elif source_type == "docx_text":
        base = "docx"
    elif source_type == "plain_text":
        base = "plain_text"
    else:
        base = "generic"

    if quality_score < 0.65:
        return f"{base}_cleaned_low_quality"
    return f"{base}_cleaned"


def build_source_hint(source_type: str) -> str:
    if source_type == "scanned_pdf_ocr":
        return (
            "입력은 OCR 결과일 가능성이 높습니다. "
            "깨진 줄바꿈, 표 선, 장식 문자, 분절된 문장, 중복 라인을 우선 정리하세요. "
            "의미 없는 짧은 조각 라인은 제거하되, 경력/기술/프로젝트 관련 정보는 최대한 보존하세요."
        )
    if source_type == "digital_pdf_text":
        return (
            "입력은 일반 PDF의 텍스트 레이어에서 추출된 결과일 가능성이 높습니다. "
            "컬럼 순서 꼬임이나 레이아웃 순서 문제로 문장 흐름이 어색할 수 있으니, "
            "같은 문맥에 속하는 줄은 자연스럽게 재배열하되 없는 내용을 추가하지 마세요."
        )
    return (
        "입력은 일부 페이지는 텍스트 레이어, 일부 페이지는 OCR 결과가 섞인 혼합형 문서일 수 있습니다. "
        "페이지 순서를 유지하면서 노이즈를 정리하고, 읽기 자연스럽게 구조를 맞춰 주세요."
    )


def build_document_hint(document_kind: str) -> str:
    if document_kind == "resume_like":
        return (
            "이 문서는 이력서 또는 경력기술서일 가능성이 높습니다. "
            "경력, 학력, 기술스택, 프로젝트, 자격증, 수상, 활동 이력을 우선적으로 구조화하세요."
        )
    if document_kind == "cover_letter_like":
        return (
            "이 문서는 자기소개서 또는 지원동기 문서일 가능성이 높습니다. "
            "문항별 질문과 답변 구조가 보이면 유지하고, 지원동기와 경험 문단을 잘 보존하세요."
        )
    if document_kind == "portfolio_layout":
        return (
            "이 문서는 포트폴리오일 가능성이 높습니다. "
            "디자인 장식 요소보다 프로젝트명, 기간, 역할, 사용기술, 문제정의, 해결방법, 성과를 우선적으로 보존하세요."
        )
    return "문서 내에서 식별 가능한 섹션과 핵심 경력 정보를 최대한 보존하면서 읽기 쉬운 구조로 정리하세요."


def should_run_llm_cleaning(
    *,
    source_type: str,
    document_kind: str,
    normalized_text: str | None,
) -> tuple[bool, str | None]:
    metrics = collect_quality_metrics(normalized_text)
    quality_score = metrics["quality_score"]
    meaningful_chars = metrics["meaningful_chars"]
    short_fragment_ratio = metrics["short_fragment_ratio"]
    noisy_line_ratio = metrics["noisy_line_ratio"]
    line_count = metrics["line_count"]

    if meaningful_chars < LLM_MIN_SOURCE_CHARS:
        return False, None
    if not (settings.OPENAI_API_KEY or "").strip():
        return False, None

    if document_kind == "portfolio_layout" and quality_score < LLM_PORTFOLIO_QUALITY_THRESHOLD:
        return True, "portfolio_layout_complex"
    if source_type == "scanned_pdf_ocr" and (
        quality_score < LLM_OCR_QUALITY_THRESHOLD
        or noisy_line_ratio > 0.08
        or short_fragment_ratio > 0.25
    ):
        return True, "ocr_quality_low"
    if source_type == "mixed_pdf" and (
        quality_score < LLM_OCR_QUALITY_THRESHOLD
        or short_fragment_ratio > 0.22
    ):
        return True, "mixed_layout_complex"
    if quality_score < LLM_LOW_QUALITY_THRESHOLD:
        return True, "quality_low"
    if line_count >= 25 and short_fragment_ratio > 0.3:
        return True, "fragmented_lines"
    return False, None


def is_llm_output_acceptable(
    *,
    source_text: str,
    candidate_text: str | None,
) -> bool:
    normalized_candidate = normalize_extracted_text(candidate_text or "")
    normalized_source = normalize_extracted_text(source_text)
    if not normalized_candidate or not normalized_source:
        return False

    source_meaningful = max(count_meaningful_chars(normalized_source), 1)
    candidate_meaningful = count_meaningful_chars(normalized_candidate)
    candidate_length_ratio = len(normalized_candidate) / max(len(normalized_source), 1)
    candidate_meaningful_ratio = candidate_meaningful / source_meaningful

    if candidate_length_ratio < LLM_MIN_ACCEPTED_LENGTH_RATIO:
        return False
    if candidate_meaningful_ratio < LLM_MIN_ACCEPTED_MEANINGFUL_RATIO:
        return False
    return True


def get_openai_client():
    client = getattr(_LLM_CLIENT_LOCAL, "openai_client", None)
    if client is not None:
        return client

    api_key = (settings.OPENAI_API_KEY or "").strip()
    if not api_key:
        return None

    try:
        from openai import OpenAI
    except ImportError:
        logger.warning("openai is not installed. LLM normalization is disabled.")
        return None

    try:
        client = OpenAI(
            api_key=api_key,
            timeout=LLM_NORMALIZATION_TIMEOUT_SECONDS,
        )
        _LLM_CLIENT_LOCAL.openai_client = client
        return client
    except Exception:
        logger.exception("Failed to initialize OpenAI client for document normalization.")
        return None


def run_llm_normalization(
    *,
    source_type: str,
    document_kind: str,
    normalized_text: str,
) -> str | None:
    client = get_openai_client()
    if client is None:
        return None

    prompt = LLM_NORMALIZATION_USER_PROMPT_TEMPLATE.format(
        source_type=source_type,
        document_type=document_kind,
        source_hint=build_source_hint(source_type),
        document_hint=build_document_hint(document_kind),
        text=normalized_text,
    )

    try:
        response = client.responses.create(
            model=LLM_NORMALIZATION_MODEL,
            input=f"{LLM_NORMALIZATION_SYSTEM_PROMPT.strip()}\n\n{prompt.strip()}",
        )
        return normalize_extracted_text(getattr(response, "output_text", "") or "")
    except Exception:
        logger.exception(
            "LLM normalization failed for source_type=%s document_type=%s",
            source_type,
            document_kind,
        )
        return None
