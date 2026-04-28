from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

'''
dataclass, 상수, 정규식, 프롬프트
'''

FILES_PREFIX = "/files"
DOCUMENT_ROOT_DIR = "documents"
CANDIDATE_DIR = "candidates"

ALLOWED_DOCUMENT_TYPES = {
    "RESUME",
    "PORTFOLIO",
    "COVER_LETTER",
    "CAREER_DESCRIPTION",
    "ROLE_PROFILE",
}

ALLOWED_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
    "txt",
    "hwp",
    "hwpx",
}

READ_CHUNK_SIZE = 1024 * 1024
OCR_RENDER_DPI = 300
MIN_DIRECT_TEXT_SCORE_FOR_SKIP_OCR = 48
MIN_DIRECT_TEXT_LENGTH_FOR_SKIP_OCR = 90
MIN_DIRECT_TEXT_KO_EN_CHARS_FOR_SKIP_OCR = 40
MIN_MERGEABLE_TEXT_SCORE = 28
MIN_OCR_SCORE_ADVANTAGE = 40
PDF_CLASSIFICATION_SAMPLE_PAGES = 3
PDF_SCANNED_TEXT_SCORE_THRESHOLD = 36
PDF_TEXT_DOCUMENT_AVG_SCORE_THRESHOLD = 95
PDF_TEXT_DOCUMENT_MIN_TEXT_PAGES = 2
OCR_LINE_GROUPING_TOLERANCE = 24
MAX_PAGES_FOR_HEADER_FOOTER_ANALYSIS = 8
MAX_REPEATED_LINE_LENGTH = 80
MAX_SHORT_NOISE_LINE_LENGTH = 3

LLM_NORMALIZATION_MODEL = "gpt-5.2"
LLM_NORMALIZATION_TIMEOUT_SECONDS = 45.0
LLM_MIN_SOURCE_CHARS = 220
LLM_LOW_QUALITY_THRESHOLD = 0.65
LLM_OCR_QUALITY_THRESHOLD = 0.82
LLM_PORTFOLIO_QUALITY_THRESHOLD = 0.9
LLM_MIN_ACCEPTED_LENGTH_RATIO = 0.35
LLM_MIN_ACCEPTED_MEANINGFUL_RATIO = 0.3

BOX_DRAWING_PATTERN = re.compile(r"^[\s|_\-~=+*/\\.,:;()[\]{}<>]+$")
PAGE_NUMBER_PATTERN = re.compile(
    r"^(?:page\s*)?\d{1,3}(?:\s*/\s*\d{1,3})?$|^-\s*\d{1,3}\s*-$",
    re.IGNORECASE,
)
LINE_NOISE_CHAR_PATTERN = re.compile(r"[|_\-~=+*/\\]")
MEANINGFUL_CHAR_PATTERN = re.compile(r"[0-9A-Za-z\u3131-\u318E\uAC00-\uD7A3]")
SECTION_HEADING_PATTERN = re.compile(
    r"^(?:"
    r"[A-Z][A-Z /&+\-]{1,40}"
    r"|"
    r"(?:기본 정보|경력|프로젝트|기술\s*스택|자기소개|지원동기|학력|자격증|수상|활동|포트폴리오|경험|역할|성과|교육|보유 역량|업무 내용|주요 업무|사용 기술|참여 기간|담당 업무)"
    r")$"
)

LLM_NORMALIZATION_SYSTEM_PROMPT = """
You are a document normalization assistant for a recruiting platform.

Your task is to clean and restructure extracted text from resumes, cover letters, and portfolios so that it can be used as input for interview-question generation.

The input text may come from:
1. OCR on scanned PDF documents
2. Direct text extraction from digital PDFs with text layers

You must preserve factual content, remove layout noise, and keep important section structure.

Do not summarize aggressively.
Do not invent or infer missing information.
Do not add content that is not present in the source text.
"""

LLM_NORMALIZATION_USER_PROMPT_TEMPLATE = """
다음은 지원자가 업로드한 문서에서 추출된 텍스트입니다.

문서 분류:
- source_type: {source_type}
- document_type: {document_type}

이 텍스트는 두 가지 경우 중 하나일 수 있습니다.

1. OCR 결과
- 표 선, 장식 요소, 반복 헤더/푸터, 줄바꿈 깨짐, OCR 노이즈가 포함될 수 있습니다.

2. 일반 PDF 텍스트 추출 결과
- OCR 오류는 적을 수 있지만, 컬럼 순서 꼬임, 표/레이아웃 순서 문제, 불필요한 줄바꿈, 숨은 텍스트, 반복 요소가 포함될 수 있습니다.

목표:
이 텍스트를 채용 면접 예상질문 생성에 적합한 일반 텍스트로 정제하세요.

반드시 지킬 규칙:
1. 원문 의미를 바꾸지 마세요.
2. 없는 정보를 추가하지 마세요.
3. 추측하지 마세요.
4. 표 선, 장식 문자, 페이지 번호, 반복 헤더/푸터는 제거하세요.
5. 경력, 학력, 프로젝트, 기술스택, 자격증, 자기소개 문단은 최대한 유지하세요.
6. 표 형태 정보는 가능하면 항목형 텍스트나 문장형 텍스트로 바꾸세요.
7. 일반 PDF에서 컬럼 순서나 줄바꿈이 어색하면 읽기 자연스럽게 재배열하세요.
8. 결과는 markdown 없이 일반 텍스트로 출력하세요.
9. 요약하지 말고, 핵심 구조를 유지한 정제 결과를 만드세요.
10. 문서 내 섹션 제목이 보이면 유지하세요.
11. 면접 질문 생성에 불필요한 민감정보(상세 주소, 주민등록번호 등)는 제거하거나 생략해도 됩니다.

추가 지시:`
{source_hint}

문서 유형 지시:
{document_hint}

출력 형식:
- 사람이 읽기 쉬운 일반 텍스트
- 섹션 단위로 정리
- bullet은 허용

입력 텍스트:
\"\"\"
{text}
\"\"\"
"""


@dataclass(slots=True)
class SavedFileResult:
    title: str
    original_file_name: str
    stored_file_name: str
    file_path: str
    file_ext: str | None
    mime_type: str | None
    file_size: int | None


@dataclass(slots=True)
class ExtractedTextResult:
    extracted_text: str | None
    extract_status: str
    extract_strategy: str = "unsupported"
    extract_quality_score: float = 0.0
    source_type: str = "unknown"
    document_type: str = "unknown"
    raw_text: str | None = None
    normalized_text: str | None = None
    extract_meta: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PageExtractionResult:
    selected_text: str | None
    direct_text: str | None
    ocr_text: str | None
    direct_score: int
    ocr_score: int
    used_ocr: bool


@dataclass(slots=True)
class PdfPageSignal:
    page_number: int
    direct_text: str | None
    direct_score: int
    meaningful_chars: int
    image_count: int
    block_count: int


@dataclass(slots=True)
class PdfDocumentSignal:
    source_type: str
    page_signals: list[PdfPageSignal]


@dataclass(slots=True)
class PageTextSnapshot:
    page_number: int
    direct_text: str | None
    selected_text: str | None
    source_mode: str
