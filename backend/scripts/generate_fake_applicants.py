"""
HR Copilot BS - 가짜 지원자 문서 생성 스크립트

목적
1. 지원자 등록용 가짜 지원자 프로필 생성
2. 실제 업로드 가능한 PDF 문서 생성
3. 지원자 유형을 별도 메타데이터로 남겨 AI 분석 품질 테스트 지원

문서 구성
- 전 직무: 이력서 + 자기소개서 합본 PDF
- AI_개발_데이터 직무: 합본 PDF + 포트폴리오 PDF + 경력기술서 PDF

실행 예시
  set OPENAI_API_KEY=sk-...
  python backend/scripts/generate_fake_applicants.py

필수 패키지
  pip install reportlab httpx
"""

from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
MODEL = os.getenv("FAKE_APPLICANT_MODEL", "gpt-4.1")
OUTPUT_DIR = BASE_DIR / "sample_data" / "fake_applicants" / "2차_지원자_문서"
DELAY_SECONDS = 0.7
HTTP_TIMEOUT_SECONDS = float(os.getenv("FAKE_APPLICANT_TIMEOUT_SECONDS", "180"))
REQUEST_RETRY_COUNT = int(os.getenv("FAKE_APPLICANT_RETRY_COUNT", "3"))
REQUEST_RETRY_DELAY_SECONDS = float(
    os.getenv("FAKE_APPLICANT_RETRY_DELAY_SECONDS", "2")
)
JOB_LIMIT = int(os.getenv("FAKE_APPLICANT_JOB_LIMIT", "0"))

JOB_DISPLAY_NAMES: dict[str, str] = {
    "HR": "HR_인사",
    "MARKETING": "마케팅광고_MD",
    "AI_DEV_DATA": "AI_개발_데이터",
    "SALES": "영업",
    "STRATEGY_PLANNING": "기획_전략",
}

FONT_CANDIDATES = [
    "C:/Windows/Fonts/malgun.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/Library/Fonts/AppleGothic.ttf",
]


@dataclass(frozen=True)
class PersonaSpec:
    slug: str
    label: str
    intent: str
    hidden_signals: list[str]
    extra_documents: list[str]


@dataclass(frozen=True)
class CandidateCaseSpec:
    code: str
    title: str
    description: str
    persona_slug: str
    must_haves: list[str]
    resume_shape: str


COMMON_PERSONAS: list[PersonaSpec] = [
    PersonaSpec(
        slug="elite_verification",
        label="검증형 우수 인재",
        intent=(
            "성과, 사고력, 표현력, 커리어 흐름이 모두 안정적으로 좋아 보이는 상위권 지원자다. "
            "서류만 보면 바로 합격권처럼 느껴지지만, 실제 면접에서는 이 성과가 우연이 아닌지, "
            "본인의 판단 기준과 문제 해결 사고가 얼마나 깊은지, 스스로 만든 원칙과 기준이 있는지를 "
            "검증해야 하는 유형이다."
        ),
        hidden_signals=[
            "성과 수치와 맥락이 자연스럽고 과장 없이 연결되어 읽힌다.",
            "업무 배경, 본인 행동, 결과, 회고가 비교적 일관되게 서술된다.",
            "자기소개서 표현이 과하지 않고 차분하지만, 기준과 관점이 느껴지게 작성한다.",
            "무조건 잘난 척하는 인상보다 깊이 있는 실무자처럼 보이게 한다.",
            "읽는 사람이 '좋아 보이는데 정말 이 사람 생각이 맞는지 더 깊게 검증하고 싶다'고 느끼게 한다.",
        ],
        extra_documents=[],
    ),
    PersonaSpec(
        slug="inflated_impact",
        label="성과 과장 의심형",
        intent=(
            "성과 수치와 임팩트는 매우 화려하게 보이지만, 실제로 본인이 어느 범위까지 기여했는지가 "
            "희미한 지원자다. 팀의 공을 개인의 공처럼 보이게 쓰거나, 본인 역할을 넓게 포장했을 가능성이 있어 "
            "면접에서 기여 범위와 실행 주체를 구체적으로 캐내야 한다."
        ),
        hidden_signals=[
            "성과 수치는 구체적으로 쓰되, 그 숫자를 본인이 직접 만든 것인지 팀 단위 결과인지 모호하게 남긴다.",
            "주도, 리드, 총괄, 주관 같은 표현을 자주 사용하지만 실제 행동 설명은 상대적으로 적게 한다.",
            "업무 성과를 설명할 때 본인 기여, 타 부서 협업, 조직 지원의 경계가 흐릿하다.",
            "프로젝트 과정 설명보다 결과 요약과 임팩트 강조에 더 많은 분량을 쓴다.",
            "읽는 사람이 '이 수치가 진짜 네가 만든 거 맞아?'라는 의심을 자연스럽게 하게 만든다.",
        ],
        extra_documents=[],
    ),
    PersonaSpec(
        slug="polished_but_shallow",
        label="포장형 지원자",
        intent=(
            "문장력과 표현은 세련됐지만 실제 경험 밀도와 실무 깊이는 얕을 수 있는 지원자다. "
            "트렌디한 키워드와 그럴듯한 문장을 잘 쓰지만, 구체적인 사례와 판단 근거는 비어 있을 가능성이 있어 "
            "실무 수준과 용어 이해도를 파고드는 질문이 필요하다."
        ),
        hidden_signals=[
            "트렌디한 표현, 추상적 비즈니스 용어, 자기계발식 문장을 자주 사용한다.",
            "문장은 매끄럽지만 구체적인 숫자, 상황, 의사결정 기준은 상대적으로 부족하다.",
            "본인이 실제로 한 행동보다 결과 요약이나 교훈 정리에 더 많은 비중을 둔다.",
            "실제 실무 장면이 눈에 그려지기보다는 발표 자료처럼 읽히게 한다.",
            "읽는 사람이 '말은 잘하는데 실제로 해본 건 얼마나 될까?'라고 느끼게 한다.",
        ],
        extra_documents=[],
    ),
    PersonaSpec(
        slug="job_fit_doubt",
        label="직무 적합도 의심형",
        intent=(
            "학력, 활동, 기본 역량은 나쁘지 않지만 현재 지원 직무와의 직접 연결이 약해 보이는 지원자다. "
            "왜 이 직무를 선택했는지, 실제로 얼마나 준비했는지, 적합성이 진짜인지 면접에서 확인해야 한다."
        ),
        hidden_signals=[
            "이전 전공이나 경험은 성실하고 우수하지만 현재 직무와 직접 연결되는 증거는 제한적이다.",
            "지원 동기와 전환 계기는 존재하지만 완전히 매끈하게 이어지지는 않는다.",
            "읽는 사람이 '좋은 사람 같긴 한데 이 직무랑 정말 맞나?'라는 의문을 갖게 만든다.",
            "서류에는 가능성이 보이되, 적합성 검증 질문이 반드시 필요하게 한다.",
        ],
        extra_documents=[],
    ),
    PersonaSpec(
        slug="job_hopper",
        label="이직 잦은형",
        intent=(
            "짧은 재직 기간이 반복되는 지원자로, 실력이 전혀 없어 보이지는 않지만 조직 적응력과 지속 근무 가능성이 "
            "걱정되는 유형이다. 면접에서는 이직 사유, 퇴사 패턴, 커리어 방향성, 협업 적응 문제를 확인해야 한다."
        ),
        hidden_signals=[
            "경력 자체는 괜찮아 보일 수 있으나 1년 내외의 짧은 재직이 반복되도록 구성한다.",
            "각 회사에서 성과나 경험은 남겼지만 깊게 쌓였다는 인상은 약하게 만든다.",
            "퇴사 사유를 직접적으로 쓰지 않고 성장, 변화, 더 큰 도전 같은 표현으로 우회한다.",
            "짧은 근속에 대한 본인 설명은 그럴듯하지만 완전히 안심되지는 않게 한다.",
            "읽는 사람이 '이번에도 금방 나갈 사람 아닐까?'라는 질문을 떠올리게 한다.",
        ],
        extra_documents=[],
    ),
    PersonaSpec(
        slug="personality_risk",
        label="인성 리스크형",
        intent=(
            "업무 성과와 역량은 일정 수준 이상으로 보이지만, 협업 태도와 책임 인식에서 조직 적합성 리스크가 "
            "느껴지는 지원자다. 면접에서는 갈등 해결 방식, 피드백 수용성, 실패 책임, 타인과의 협업 태도를 "
            "중점적으로 검증해야 한다."
        ),
        hidden_signals=[
            "성과를 설명할 때 본인의 기여를 과도하게 강조하고 동료나 타 부서의 기여는 자연스럽게 축소한다.",
            "협업 사례를 쓸 때 조율과 설득을 강조하지만, 실제 문장 뉘앙스는 상대의 비협조와 무능을 문제로 삼는다.",
            "갈등 경험 문항에서 본인의 성찰보다 상대의 태도 문제와 조직의 비효율을 더 길게 설명한다.",
            "실패 경험을 서술할 때 책임을 완전히 인정하기보다 외부 환경, 의사결정권자, 프로세스 문제로 분산시킨다.",
            "자신감은 높지만 겸손, 학습 태도, 피드백 수용성은 충분히 드러나지 않게 한다.",
            "읽는 사람이 '성과는 있는데 같이 일하기 편한 사람일까?'라는 의문을 갖게 하되, 노골적 비호감으로 보이진 않게 한다.",
        ],
        extra_documents=[],
    ),
    PersonaSpec(
        slug="career_gap_switch",
        label="공백 및 전환형",
        intent=(
            "공백기, 진로 변경, 직무 전환이 있어 서류만으로는 배경 설명이 충분하지 않은 지원자다. "
            "전환 동기와 준비 과정이 진짜인지, 공백 기간 동안 어떤 학습과 실전 노력이 있었는지, "
            "이번 지원이 일시적 선택인지 확인해야 하는 유형이다."
        ),
        hidden_signals=[
            "경력 흐름 중 공백기나 직무 전환 구간이 존재하지만 설명은 지나치게 길지 않게 남긴다.",
            "전환 동기는 납득 가능하게 쓰되, 실제로 얼마나 준비했는지는 면접에서 더 확인하고 싶게 한다.",
            "학습, 자격증, 프로젝트, 개인 활동 등이 일부 보이지만 실전 강도는 애매하게 설계한다.",
            "이전 경력과 현재 지원 직무 사이 연결고리는 그럴듯하되 완전히 매끈하지는 않게 한다.",
            "읽는 사람이 '의지는 있는 것 같은데 정말 준비가 충분한가?'라고 생각하게 만든다.",
        ],
        extra_documents=[],
    ),
    PersonaSpec(
        slug="high_potential_junior",
        label="잠재력 높은 신입형",
        intent=(
            "실무 경력은 부족하거나 없지만 프로젝트 경험, 문제 해결 방식, 학습 속도, 사고 구조에서 강점이 보이는 "
            "신입 또는 주니어 지원자다. 면접에서는 포텐셜이 실제 업무 수행으로 이어질 수 있는지, "
            "기초 이해가 단단한지 검증해야 한다."
        ),
        hidden_signals=[
            "학교, 대외활동, 공모전, 사이드 프로젝트의 밀도가 높고 비교적 성실하게 쌓여 있다.",
            "큰 성과는 아니어도 문제를 구조적으로 바라본 흔적과 학습 과정이 드러난다.",
            "자기소개서에서 성장 배경과 배운 점이 설득력 있게 연결된다.",
            "경험 규모는 작지만 생각의 깊이나 태도는 좋게 느껴지게 한다.",
            "읽는 사람이 '경험은 적지만 잘 키우면 크게 성장할 수 있겠다'고 느끼게 만든다.",
        ],
        extra_documents=[],
    ),
    PersonaSpec(
        slug="brand_name_ambiguous",
        label="대기업 출신 애매형",
        intent=(
            "이력서에 유명 기업이나 인지도 높은 조직 이름이 있어 첫인상은 좋지만, 실제 본인 성과와 역할은 선명하지 "
            "않은 지원자다. 브랜드 파워 뒤에 가려진 실제 기여도와 독립적인 역량을 면접에서 벗겨내야 한다."
        ),
        hidden_signals=[
            "유명 기업, 대형 프로젝트, 잘 알려진 서비스 경험이 포함되지만 담당 범위는 넓고 추상적으로 적는다.",
            "정량 지표보다 조직명, 브랜드명, 프로젝트 스케일에 기대는 인상이 나게 한다.",
            "조직 내 역할이 일부 보이지만 의사결정 권한과 실질적 책임 범위는 모호하게 남긴다.",
            "읽는 사람이 '회사 이름은 좋은데 정작 이 사람이 한 일은 뭐지?'라고 느끼게 만든다.",
        ],
        extra_documents=[],
    ),
    PersonaSpec(
        slug="specialist_narrow",
        label="전문성 편향형",
        intent=(
            "특정 기술, 특정 산업, 특정 업무 영역에는 매우 강해 보이지만 확장성이나 협업 유연성이 충분한지는 "
            "확신하기 어려운 지원자다. 면접에서는 범용 문제 해결력, 타 영역과의 협업, 새로운 환경 적응력을 확인해야 한다."
        ),
        hidden_signals=[
            "특정 영역 성과와 전문성은 강하게 드러나지만 다른 문제 영역 경험은 제한적으로 보이게 한다.",
            "기술 또는 실무 깊이는 좋지만 다양한 이해관계자와의 협업 흔적은 적게 드러난다.",
            "새로운 환경에서의 적응이나 역할 확장 사례는 상대적으로 부족하게 만든다.",
            "깊이는 분명히 있어 보이되, 팀 상황에 따라 유연하게 움직일 사람인지는 애매하게 만든다.",
            "읽는 사람이 '이 사람은 좁고 깊게는 강한데, 우리 조직 맥락에서도 잘할까?'를 고민하게 만든다.",
        ],
        extra_documents=[],
    ),
    PersonaSpec(
        slug="fake_career_suspect",
        label="가라 경력 의심형",
        intent=(
            "완전히 허술해서 바로 티 나는 수준은 아니지만, 경력 기간, 기술 조합, 직책, 성과 스케일이 어딘가 "
            "부자연스러운 지원자다. 면접에서 구체 사례, 연도 흐름, 기술 사용 방식, 실제 산출물 수준을 물으면 "
            "진위가 흔들릴 수 있는 유형으로 설계한다."
        ),
        hidden_signals=[
            "재직 기간 대비 직책이나 담당 범위가 과도하게 화려하게 보이도록 만든다.",
            "사용 기술, 프로젝트 난이도, 성과 규모 조합이 미묘하게 과장된 인상을 주게 한다.",
            "연도 흐름이나 프로젝트 병행 시점이 얼핏 자연스러워 보이지만 자세히 보면 어색한 구간이 있게 한다.",
            "성과 설명은 자신감 있게 쓰되, 실제 산출물이나 의사결정 근거는 구체성이 약하게 남긴다.",
            "읽는 사람이 '뭔가 말은 되는데 자세히 물어보면 흔들릴 것 같다'고 느끼게 만든다.",
        ],
        extra_documents=[],
    ),
]


AI_DEV_EXTRA_DOCUMENTS = ["portfolio", "career_description"]

JOB_DETAIL_GUIDES: dict[str, str] = {
    "HR_인사": (
        "HR 직무는 채용 운영, 평가/보상, 조직문화, 교육, 인사제도, 노무 대응, 데이터 기반 HR 분석 중 "
        "어떤 축을 담당했는지 분명히 드러나야 한다. 성과는 단순히 '운영했다'가 아니라 채용 리드타임 단축, "
        "입사 후 조기 이탈률 감소, 평가 제도 개편, 교육 이수율 향상, 직원 만족도 개선 같은 형태로 구체화한다. "
        "현업 부서와의 조율, 제도 설계 논리, 민감한 이슈 대응 방식도 서류에 자연스럽게 묻어나게 한다."
    ),
    "마케팅광고_MD": (
        "마케팅/광고/MD 직무는 브랜드 운영, 캠페인 성과, 매출 기여, 상품 소싱, 프로모션 기획, 채널 운영, "
        "콘텐츠 기획, 광고 효율 개선 중 어떤 경험이 중심인지 분명해야 한다. ROAS, CTR, 전환율, 재구매율, "
        "카테고리 매출, 신규 입점 성과 등 구체 지표를 자연스럽게 넣고, 숫자가 없는 경우에도 소비자 인사이트와 "
        "실행 맥락이 드러나게 작성한다."
    ),
    "AI_개발_데이터": (
        "AI 개발/데이터 직무는 데이터 수집, 전처리, 모델링, 평가, 배포, 모니터링, MLOps, 장애 대응, "
        "실서비스 반영 경험 중 무엇을 주도했는지가 분명해야 한다. Python, SQL, Airflow, Spark, "
        "TensorFlow, PyTorch, FastAPI, Docker, 클라우드 등 실제 사용할 법한 도구를 자연스럽게 쓰고, "
        "성능 개선, 추론 비용 절감, 데이터 품질 향상, 운영 자동화 같은 실무 지표를 넣는다."
    ),
    "영업": (
        "영업 직무는 산업군, 담당 고객 유형, 리드 발굴 방식, 제안/협상/수주 경험, 매출 또는 계약 성과가 살아 있어야 한다. "
        "단순히 '영업을 잘한다'가 아니라 신규 고객 발굴 수, 재계약률, 매출 성장률, 파이프라인 관리, 장기 고객 유지, "
        "CS와의 연계 등 실제 영업 실무 장면이 보이게 작성한다."
    ),
    "기획_전략": (
        "기획/전략 직무는 문제 정의, 시장/데이터 분석, 실행안 설계, 우선순위 판단, 이해관계자 조율, 사업 검토, "
        "운영 개선 경험이 보여야 한다. 단순히 '전략적 사고'라고 쓰지 말고, 어떤 문제를 어떤 프레임으로 분석했고 "
        "어떤 의사결정을 내렸는지, 어떤 결과를 냈는지 드러나게 한다."
    ),
}

STYLE_GUIDES: dict[str, str] = {
    "elite_verification": (
        "문체는 차분하고 밀도 있게 작성한다. 허세나 과장 대신 판단 기준과 회고가 살아 있어야 한다. "
        "읽는 사람이 안정감과 깊이를 느끼게 한다."
    ),
    "inflated_impact": (
        "문체는 자신감 있고 화려하게 작성한다. 숫자와 임팩트를 자주 언급하되, 기여 범위는 약간 흐리게 남긴다."
    ),
    "polished_but_shallow": (
        "문체는 세련되고 발표 자료처럼 정리된 느낌으로 작성한다. 표현은 좋은데 구체성은 다소 부족하게 한다."
    ),
    "job_fit_doubt": (
        "문체는 성실하고 설득적이게 작성한다. 좋아 보이는 배경은 드러나지만 현재 직무와의 직접 연결은 완전히 확신되지 않게 한다."
    ),
    "job_hopper": (
        "문체는 커리어 의식이 강하고 전향적인 느낌으로 작성한다. 잦은 이동을 성장과 도전 서사로 포장한다."
    ),
    "personality_risk": (
        "문체는 자신감 있고 단호하게 작성한다. 본인의 영향력과 성과를 강조하되, 협업 서술에서 미묘한 불편함이 남게 한다."
    ),
    "career_gap_switch": (
        "문체는 성찰적이고 설명형으로 작성한다. 왜 전환했는지, 무엇을 준비했는지 자신의 이야기를 충분히 풀어쓴다."
    ),
    "high_potential_junior": (
        "문체는 성실하고 구체적인 성장 서사 중심으로 작성한다. 거창한 성공보다 배우고 쌓아온 흔적이 잘 보이게 한다."
    ),
    "brand_name_ambiguous": (
        "문체는 안정적이고 정돈되어 보이게 작성한다. 좋은 회사 경험은 드러나지만, 본인 역할은 완전히 선명하지 않게 한다."
    ),
    "specialist_narrow": (
        "문체는 실무자답고 기술적이게 작성한다. 특정 분야 깊이는 보이되 시야가 넓다는 인상은 과도하게 주지 않는다."
    ),
    "fake_career_suspect": (
        "문체는 자신감 있고 그럴듯하게 작성한다. 다만 자세히 읽으면 경력 스케일이나 조합이 살짝 과해 보이게 한다."
    ),
}


def build_persona_lookup() -> dict[str, PersonaSpec]:
    return {persona.slug: persona for persona in COMMON_PERSONAS}


def build_common_case_specs() -> list[CandidateCaseSpec]:
    return [
        CandidateCaseSpec(
            code="new_grad_standard",
            title="완전 신입 - 정상적 신입",
            description=(
                "정규직 경력이 전혀 없는 전형적인 신입 지원자다. 학력, 대외활동, 팀프로젝트, 교육, 자격증, "
                "아르바이트 또는 교내 경험을 중심으로 서류를 구성한다. 지나치게 과장되지 않고 무난한 신입처럼 보여야 한다."
            ),
            persona_slug="high_potential_junior",
            must_haves=[
                "정규직 경력 없음",
                "학교 프로젝트 또는 대외활동 중심",
                "과장되지 않은 무난한 신입 서사",
            ],
            resume_shape="experience는 비워도 된다. 대신 projects, activities, 학습 경험을 풍부하게 채운다.",
        ),
        CandidateCaseSpec(
            code="new_grad_parenting_gap",
            title="완전 신입 - 조기 출산 및 육아로 늦어진 신입",
            description=(
                "나이는 30세 안팎이지만 사실상 사회 경력이 없는 신입이다. 이른 출산과 육아로 인해 일반적인 취업 시점이 "
                "늦어졌고, 최근 다시 취업을 준비한 배경이 있다. 공백 사유는 숨기지 않되 지나치게 비극적으로 쓰지 말고 "
                "복귀 의지와 준비 과정을 보여줘야 한다."
            ),
            persona_slug="career_gap_switch",
            must_haves=[
                "사회경험이 거의 없음",
                "육아로 인한 공백 설명 존재",
                "복귀 준비 과정과 의지 표현",
            ],
            resume_shape="experience는 없거나 단기 활동만 있고, cover_letter에 복귀 맥락을 충분히 담는다.",
        ),
        CandidateCaseSpec(
            code="intern_many_no_conversion",
            title="인턴 경험 신입 - 인턴은 많지만 정규직 전환 없음",
            description=(
                "인턴 경험과 스펙은 좋지만 정규직 전환이 한 번도 되지 않은 신입이다. 서류만 봐도 왜 계속 인턴에서 끝났는지 "
                "궁금해지는 결이 있어야 한다. 직접적인 결격사유는 드러나지 않지만 사회성이나 조직 적응력에 대한 합리적 "
                "의심이 들 수 있게 구성한다."
            ),
            persona_slug="personality_risk",
            must_haves=[
                "인턴 경험 2회 이상",
                "정규직 전환 실패 이력",
                "스펙은 좋은데 조직 적응 의문",
            ],
            resume_shape="experience는 인턴 위주로 구성하고, collaboration 서술에 미묘한 불편함을 남긴다.",
        ),
        CandidateCaseSpec(
            code="intern_top_spec",
            title="인턴 경험 신입 - 인턴/자격증/봉사 모두 좋은 엄친아형",
            description=(
                "인턴, 자격증, 봉사활동, 교내외 활동이 모두 안정적으로 좋은 모범생형 신입이다. 지나친 과장보다 성실성과 "
                "준비성이 잘 보이는 서류여야 하며, 면접에서는 깊이와 실제 실무 전환 가능성을 검증하고 싶게 만들어야 한다."
            ),
            persona_slug="elite_verification",
            must_haves=[
                "인턴 경험 좋음",
                "자격증/봉사활동/대외활동 고르게 좋음",
                "안정적이고 모범적인 인상",
            ],
            resume_shape="education, internships, projects를 균형 있게 채우고 자기소개서는 차분하게 작성한다.",
        ),
        CandidateCaseSpec(
            code="high_edu_nonmajor",
            title="전공 불일치 신입 - 학력은 높고 기존 전공 성취도도 좋음",
            description=(
                "지원 직무 전공은 아니지만 기존 전공에서 학점, 자격증, 수상경력 등은 좋은 편인 신입이다. 전공은 다르지만 "
                "성실하고 역량 있는 사람으로 보이며, 왜 지금 직무로 오게 되었는지 설득력이 관건이다."
            ),
            persona_slug="job_fit_doubt",
            must_haves=[
                "전공 불일치",
                "기존 전공 학점/수상/자격증 우수",
                "새 직무로 넘어오는 이유가 중요",
            ],
            resume_shape="기존 전공 성취를 잘 보여주되, 새 직무와의 연결 근거를 반드시 넣는다.",
        ),
        CandidateCaseSpec(
            code="career_switch_unrelated_major",
            title="직무전환형 - 원예/미술 등 완전 무관 배경",
            description=(
                "원예, 미술 등 완전히 다른 전공과 직무 배경을 가졌고, 기존 일에 회의를 느껴 새 직무로 전환하려는 지원자다. "
                "도망치듯 온 것인지, 진지하게 준비한 것인지 면접에서 가려내고 싶게 만들어야 한다."
            ),
            persona_slug="career_gap_switch",
            must_haves=[
                "기존 전공과 현재 지원 직무가 완전히 다름",
                "기존 직무 불만 또는 회의감 존재",
                "새 직무 준비 흔적 필요",
            ],
            resume_shape="이전 경력/전공은 유지하되 새로운 학습 기록, 사이드 프로젝트, 자격증을 넣는다.",
        ),
        CandidateCaseSpec(
            code="career_gap_bullying",
            title="경력단절 복귀 - 직장 내 괴롭힘 퇴사 후 2년 공백",
            description=(
                "직장 내 괴롭힘으로 퇴사한 뒤 약 2년 정도 경력 공백이 있었고, 최근 다시 사회로 나오려는 지원자다. "
                "피해 서사를 과도하게 늘어놓기보다 조심스럽고 현실적인 복귀 서사로 작성해야 하며, 적응 가능성이 "
                "궁금해지게 해야 한다."
            ),
            persona_slug="career_gap_switch",
            must_haves=[
                "직장 내 괴롭힘 퇴사",
                "2년 전후 공백",
                "복귀 의지는 있으나 적응 우려 존재",
            ],
            resume_shape="공백 설명을 cover_letter에 담고, 퇴사 이유는 절제된 톤으로 서술한다.",
        ),
        CandidateCaseSpec(
            code="career_gap_unpaid_wage_treatment",
            title="경력단절 복귀 - 임금체불 퇴사 후 의지 상실과 치료 이력",
            description=(
                "임금체불로 퇴사한 후 심리적으로 크게 위축되어 정신과 치료를 받은 이력이 있고, 한동안 취업 의지를 잃었다가 "
                "최근 다시 복귀를 준비한 지원자다. 너무 극적으로 쓰지 말고 현실적이면서도 조심스러운 복귀 맥락이 느껴져야 한다."
            ),
            persona_slug="career_gap_switch",
            must_haves=[
                "임금체불 퇴사",
                "치료 이력 또는 회복 서사",
                "신중한 복귀 준비",
            ],
            resume_shape="강한 피해자 서사보다 회복과 재준비 중심으로 구성한다.",
        ),
        CandidateCaseSpec(
            code="job_hopper_weak_evidence",
            title="이직 많음 - 포장은 잘 되어 있으나 근거 부족",
            description=(
                "이직이 잦고 서류 포장은 꽤 잘했지만 각 회사에서 실제로 뭘 했는지 근거가 약하다. 이직 사유도 명확하지 않아 "
                "면접관이 반복적으로 이동한 이유를 캐묻게 되는 지원자다."
            ),
            persona_slug="inflated_impact",
            must_haves=[
                "짧은 재직 반복",
                "성과 표현은 화려함",
                "이직 사유가 불분명함",
            ],
            resume_shape="experience는 여러 회사로 쪼개고, 성과는 화려하지만 디테일은 다소 비어 있게 한다.",
        ),
        CandidateCaseSpec(
            code="job_hopper_conflict_blame",
            title="이직 많음 - 인성 리스크가 느껴지는 케이스",
            description=(
                "이직이 잦은데, 팀원과의 불화 경험을 적어놓은 부분에서 남탓이 많고 본인 성찰은 약하다. 서류만 봐도 "
                "갈등 원인이 늘 외부에 있었던 것처럼 보여 면접에서 협업 태도를 검증하고 싶게 만들어야 한다."
            ),
            persona_slug="personality_risk",
            must_haves=[
                "이직이 많음",
                "갈등 경험에서 남탓 뉘앙스",
                "인성 리스크 단서 존재",
            ],
            resume_shape="collaboration/failure_learning에 갈등 서사를 넣고 책임 분산 뉘앙스를 남긴다.",
        ),
        CandidateCaseSpec(
            code="career_general_top",
            title="일반 경력직 - 우수 인재",
            description=(
                "전형적인 경력직이며 실제로도 상당히 우수해 보이는 지원자다. 경력 흐름, 성과 수치, 자소서 논리가 안정적이고 "
                "좋아서 서류만 봐도 면접으로 불러보고 싶지만, 진짜 깊이와 기준을 확인하고 싶게 만들어야 한다."
            ),
            persona_slug="elite_verification",
            must_haves=[
                "경력 흐름 안정적",
                "성과와 역할이 일관됨",
                "과장보다 깊이 검증이 필요한 상위 지원자",
            ],
            resume_shape="experience 중심으로 디테일하게 구성하고 자기소개서도 차분하고 깊게 쓴다.",
        ),
        CandidateCaseSpec(
            code="career_general_overwritten",
            title="일반 경력직 - 기간 대비 너무 많은 걸 적은 케이스",
            description=(
                "경력직이긴 한데 재직 기간과 직급에 비해 지나치게 많은 역할과 성과를 적어놓아 검증이 필요한 지원자다. "
                "겉보기에는 화려하지만 자세히 보면 실제 범위가 궁금해지는 문서가 되어야 한다."
            ),
            persona_slug="fake_career_suspect",
            must_haves=[
                "재직 기간 대비 과도한 범위",
                "성과/역할 조합이 조금 과함",
                "깊게 물으면 흔들릴 여지",
            ],
            resume_shape="성과와 범위를 넓게 적되 세부 근거는 완전히 충족시키지 않는다.",
        ),
    ]


def build_ai_extra_case_specs() -> list[CandidateCaseSpec]:
    return [
        CandidateCaseSpec(
            code="it_bootcamp_new_grad_overwritten",
            title="IT 부트캠프 비전공자 - 완전 신입인데 포트폴리오가 과도하게 화려함",
            description=(
                "비전공자 부트캠프 출신의 완전 신입인데 포트폴리오와 자기소개서를 그럴듯하게 매우 잘 써놨다. "
                "하지만 부트캠프 기간 대비 너무 많은 것을 했고, 본인이 정확히 무엇을 했는지 근거가 부족해 보인다. "
                "읽는 사람이 논리적으로 짧은 기간 안에 이 정도를 다 배웠다고 의심하게 만들어야 한다."
            ),
            persona_slug="fake_career_suspect",
            must_haves=[
                "비전공자 부트캠프 출신",
                "완전 신입",
                "포트폴리오는 화려하지만 기여 근거 약함",
                "짧은 기간 대비 과한 스택과 산출물",
            ],
            resume_shape="experience는 거의 없고, bootcamp 프로젝트와 portfolio를 과도하게 풍성하게 작성한다.",
        ),
        CandidateCaseSpec(
            code="it_bootcamp_career_switch_stable",
            title="IT 부트캠프 비전공자 - 사회경험 있는 직무전환 무난형",
            description=(
                "다른 직무 사회경험이 있고, 부트캠프 수료 후 개발/데이터 직무로 전환한 지원자다. 공부를 열심히 한 흔적이 "
                "있고 자격증도 단기간에 3개 취득했다. 서류상으로 거짓말 같지는 않으며 전반적으로 무난하고 성실한 전환 사례처럼 보여야 한다."
            ),
            persona_slug="career_gap_switch",
            must_haves=[
                "기존 사회경험 존재",
                "부트캠프 후 전환",
                "자격증 3개 취득",
                "거짓말보다는 무난한 준비형",
            ],
            resume_shape="이전 직무 경험과 부트캠프 학습을 모두 보여주고, portfolio는 성실하고 현실적인 수준으로 구성한다.",
        ),
    ]


def build_case_plan() -> dict[str, list[CandidateCaseSpec]]:
    common_cases = build_common_case_specs()
    plan = {
        "HR": list(common_cases),
        "MARKETING": list(common_cases),
        "SALES": list(common_cases),
        "STRATEGY_PLANNING": list(common_cases),
        "AI_DEV_DATA": list(common_cases) + build_ai_extra_case_specs(),
    }
    return plan


def register_korean_font() -> str:
    for font_path in FONT_CANDIDATES:
        if Path(font_path).exists():
            pdfmetrics.registerFont(TTFont("Korean", font_path))
            return "Korean"
    return "Helvetica"


def build_styles(font_name: str) -> dict[str, ParagraphStyle]:
    getSampleStyleSheet()
    return {
        "name": ParagraphStyle(
            "Name",
            fontName=font_name,
            fontSize=22,
            leading=28,
            textColor=colors.HexColor("#111827"),
            spaceAfter=4,
        ),
        "meta": ParagraphStyle(
            "Meta",
            fontName=font_name,
            fontSize=9,
            leading=14,
            textColor=colors.HexColor("#4b5563"),
        ),
        "section": ParagraphStyle(
            "Section",
            fontName=font_name,
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#111827"),
            spaceBefore=14,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body",
            fontName=font_name,
            fontSize=9,
            leading=15,
            textColor=colors.HexColor("#1f2937"),
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            fontName=font_name,
            fontSize=9,
            leading=15,
            textColor=colors.HexColor("#1f2937"),
            leftIndent=10,
        ),
        "sub": ParagraphStyle(
            "Sub",
            fontName=font_name,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#111827"),
            spaceBefore=8,
            spaceAfter=4,
        ),
    }


def build_prompt(
    job_display_name: str,
    persona: PersonaSpec,
    case_spec: CandidateCaseSpec,
    index: int,
) -> str:
    extra_doc_note = (
        "추가 문서로 포트폴리오와 경력기술서 내용도 반드시 포함하세요."
        if "portfolio" in persona.extra_documents
        else "추가 문서는 필요 없습니다."
    )
    job_guide = JOB_DETAIL_GUIDES[job_display_name]
    style_guide = STYLE_GUIDES[persona.slug]

    return f"""
당신은 한국 기업 채용 프로세스용 테스트 데이터를 설계하는 전문가입니다.
아래 조건에 맞는 가짜 지원자 1명의 서류 원본 데이터를 JSON으로 생성하세요.

프로젝트 목적:
- 이 데이터는 HR Copilot이 서류를 분석하고 면접 질문을 생성하는지 검증하는 테스트용입니다.
- 따라서 단순히 예쁜 이력서가 아니라, 면접에서 검증해야 할 포인트가 살아 있는 문서여야 합니다.

직무: {job_display_name}
지원자 순번: {index + 1}
지원자 케이스: {case_spec.title}
지원자 유형: {persona.label}
유형 의도: {persona.intent}
케이스 설명:
- {case_spec.description}
숨겨진 검증 포인트:
- {"; ".join(persona.hidden_signals)}
반드시 드러나야 하는 케이스 요소:
- {"; ".join(case_spec.must_haves)}
이력서 구조 가이드:
- {case_spec.resume_shape}
직무 디테일 가이드:
- {job_guide}
문체 가이드:
- {style_guide}

중요 규칙:
- 실제 한국 취업 시장에서 볼 법한 자연스러운 문체로 작성하세요.
- 문서 안에 "지원자 유형", "테스트용", "가짜 데이터" 같은 말은 절대 넣지 마세요.
- 일부 지원자는 매우 우수하게, 일부는 애매하게, 일부는 과장이나 리스크가 느껴지게 작성하세요.
- 허점은 면접에서 캐야 드러나는 수준으로 설계하세요. 너무 노골적으로 이상하게 쓰지 마세요.
- 이름, 회사명, 학교명, 성과 수치, 프로젝트명은 현실적으로 작성하세요.
- 연락처와 이메일은 가짜여도 자연스러운 형식을 지키세요.
- 이력서가 단순 요약 메모처럼 보이지 않게, 실제 제출 서류처럼 맥락과 배경 설명을 충분히 넣으세요.
- 지원자가 어떤 산업/회사/문제를 다뤘는지 눈에 그려질 정도로 디테일을 넣으세요.
- 자기소개서는 지원 동기, 강점, 협업/갈등 경험, 실패/학습 경험, 입사 후 포부를 자연스럽게 반영하세요.
- 자기소개서 각 문항은 모범답안처럼 짧게 끝내지 말고, 본인 경험과 생각을 충분히 서술하세요.
- 단순히 '데이터 기반', '문제 해결', '협업 역량' 같은 추상어 반복을 피하고, 실제 상황과 본인 판단을 보여주세요.
- 직무별 용어, 성과 지표, 협업 상대, 사용 도구, 의사결정 맥락이 문서에 자연스럽게 녹아 있어야 합니다.
- 서로 다른 지원자가 정말 다른 사람처럼 보이도록 문체, 강조 포인트, 커리어 톤, 자기서사를 구분하세요.
- 케이스상 경력이 없어야 자연스러운 경우에는 정규직 경력을 억지로 만들지 마세요.
- 케이스상 공백기, 육아, 치료, 괴롭힘, 임금체불, 어학연수, 부트캠프 수료 등 배경이 필요한 경우 반드시 서류에 반영하세요.
- 완전 신입, 인턴 위주 신입, 경력직, 경력단절 복귀, 직무전환, 이직 다수 케이스가 문서 구조 자체에서 구분되게 하세요.
- {extra_doc_note}

아래 JSON 구조만 반환하세요. 마크다운 코드블록 없이 JSON만 반환하세요.

{{
  "candidate_profile": {{
    "name": "홍길동",
    "birth_year": 1995,
    "phone": "010-1234-5678",
    "email": "sample@example.com",
    "address": "서울시 강서구",
    "summary": "지원자를 요약하는 3~5문장 소개",
    "job_category": "{job_display_name}"
  }},
  "resume": {{
    "education": [
      {{
        "school": "대학교명",
        "major": "전공",
        "degree": "학사",
        "period": "2014.03 ~ 2018.02",
        "gpa": "3.8 / 4.5"
      }}
    ],
    "experience": [
      {{
        "company": "회사명",
        "department": "부서명",
        "position": "직책",
        "period": "2019.01 ~ 2022.06",
        "duties": [
          "담당 업무와 성과 1",
          "담당 업무와 성과 2",
          "담당 업무와 성과 3",
          "담당 업무와 성과 4"
        ]
      }}
    ],
    "activities": [
      "대외활동 또는 부트캠프 또는 봉사활동 또는 공백기 중 수행한 준비 1",
      "대외활동 또는 부트캠프 또는 봉사활동 또는 공백기 중 수행한 준비 2"
    ],
    "career_gap_note": "공백기나 경력단절이 있는 경우 2~4문장으로 설명, 없으면 빈 문자열",
    "projects": [
      {{
        "name": "프로젝트명",
        "period": "2023.01 ~ 2023.06",
        "role": "역할",
        "highlights": [
          "핵심 수행 내용 1",
          "핵심 수행 내용 2",
          "핵심 수행 내용 3"
        ]
      }}
    ],
    "skills": ["역량1", "역량2", "역량3", "역량4", "역량5", "역량6"],
    "certifications": ["자격증1", "자격증2", "자격증3"]
  }},
  "cover_letter": {{
    "motivation": "지원 동기 6~9문장",
    "strengths": "핵심 역량 및 경험 8~12문장",
    "collaboration": "협업 또는 갈등 경험 6~9문장",
    "failure_learning": "실패 및 학습 경험 6~9문장",
    "aspiration": "입사 후 포부 4~6문장"
  }},
  "portfolio": {{
    "required": {str("portfolio" in persona.extra_documents).lower()},
    "title": "포트폴리오 제목",
    "overview": "포트폴리오 2~4문장 설명",
    "projects": [
      {{
        "name": "프로젝트명",
        "goal": "목표",
        "stack": ["기술1", "기술2", "기술3"],
        "contribution": "본인 기여 설명 3~5문장",
        "impact": "성과 설명 2~4문장",
        "trouble_shooting": "문제 해결 사례 3~5문장"
      }}
    ]
  }},
  "career_description": {{
    "required": {str("career_description" in persona.extra_documents).lower()},
    "summary": "경력기술서 요약 3~5문장",
    "entries": [
      {{
        "company": "회사명",
        "period": "기간",
        "scope": "담당 범위 2~4문장",
        "achievements": [
          "성과 1",
          "성과 2",
          "성과 3"
        ],
        "collaboration": "협업 방식 2~4문장",
        "tools": ["툴1", "툴2", "툴3"]
      }}
    ]
  }}
}}
"""


def call_openai_json(prompt: str) -> dict[str, Any]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    payload = {
        "model": MODEL,
        "response_format": {"type": "json_object"},
        "temperature": 1.0,
        "messages": [
            {
                "role": "system",
                "content": "You generate realistic Korean recruiting documents as structured JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
    }
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    last_error: Exception | None = None

    for attempt in range(1, REQUEST_RETRY_COUNT + 1):
        try:
            with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS) as client:
                response = client.post(OPENAI_URL, headers=headers, json=payload)
                response.raise_for_status()

            message = response.json()["choices"][0]["message"]["content"]
            return json.loads(message)
        except (httpx.TimeoutException, httpx.HTTPError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt == REQUEST_RETRY_COUNT:
                break
            print(
                f"\n    재시도 {attempt}/{REQUEST_RETRY_COUNT - 1} - API 응답 지연 또는 파싱 실패",
                end="",
                flush=True,
            )
            time.sleep(REQUEST_RETRY_DELAY_SECONDS * attempt)

    assert last_error is not None
    raise last_error


def safe_slug(value: str) -> str:
    allowed = []
    for char in value.strip():
        if char.isalnum() or char in {"_", "-"}:
            allowed.append(char)
        elif char in {" ", "/"}:
            allowed.append("_")
    normalized = "".join(allowed).strip("_")
    return normalized or "candidate"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def append_section_title(
    story: list[Any], text: str, styles: dict[str, ParagraphStyle]
) -> None:
    story.append(Paragraph(text, styles["section"]))
    story.append(
        HRFlowable(
            width="100%", thickness=0.8, color=colors.HexColor("#d1d5db"), spaceAfter=6
        )
    )


def build_resume_bundle_pdf(
    data: dict[str, Any], output_path: Path, font_name: str
) -> None:
    styles = build_styles(font_name)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
    )
    story: list[Any] = []
    profile = data["candidate_profile"]
    resume = data["resume"]
    cover = data["cover_letter"]

    story.append(Paragraph(profile.get("name", ""), styles["name"]))
    story.append(Paragraph(profile.get("summary", ""), styles["meta"]))
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            " | ".join(
                filter(
                    None,
                    [
                        profile.get("phone", ""),
                        profile.get("email", ""),
                        profile.get("address", ""),
                        f"출생년도 {profile.get('birth_year', '')}",
                    ],
                )
            ),
            styles["meta"],
        )
    )
    story.append(Spacer(1, 8))

    append_section_title(story, "학력", styles)
    for item in resume.get("education", []):
        line = (
            f"<b>{item.get('school', '')}</b> "
            f"{item.get('major', '')} ({item.get('degree', '')}) | "
            f"{item.get('period', '')} | GPA {item.get('gpa', '')}"
        )
        story.append(Paragraph(line, styles["body"]))
        story.append(Spacer(1, 3))

    append_section_title(story, "경력", styles)
    for item in resume.get("experience", []):
        line = (
            f"<b>{item.get('company', '')}</b> "
            f"{item.get('department', '')} / {item.get('position', '')} | "
            f"{item.get('period', '')}"
        )
        story.append(Paragraph(line, styles["body"]))
        for duty in item.get("duties", []):
            story.append(Paragraph(f"- {duty}", styles["bullet"]))
        story.append(Spacer(1, 5))

    append_section_title(story, "프로젝트 및 주요 경험", styles)
    for item in resume.get("projects", []):
        line = f"<b>{item.get('name', '')}</b> | {item.get('period', '')} | 역할: {item.get('role', '')}"
        story.append(Paragraph(line, styles["body"]))
        for highlight in item.get("highlights", []):
            story.append(Paragraph(f"- {highlight}", styles["bullet"]))
        story.append(Spacer(1, 5))

    activities = [item for item in resume.get("activities", []) if item]
    if activities:
        append_section_title(story, "대외활동 및 추가 경험", styles)
        for activity in activities:
            story.append(Paragraph(f"- {activity}", styles["bullet"]))
        story.append(Spacer(1, 5))

    career_gap_note = (resume.get("career_gap_note") or "").strip()
    if career_gap_note:
        append_section_title(story, "공백기 및 복귀 배경", styles)
        story.append(Paragraph(career_gap_note, styles["body"]))
        story.append(Spacer(1, 5))

    append_section_title(story, "보유 역량", styles)
    table = Table(
        [
            ["기술 및 역량", " / ".join(resume.get("skills", []))],
            ["자격증 및 어학", " / ".join(resume.get("certifications", []))],
        ],
        colWidths=[34 * mm, None],
    )
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEADING", (0, 0), (-1, -1), 14),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1f2937")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)

    append_section_title(story, "자기소개서", styles)
    sections = [
        ("지원 동기", cover.get("motivation", "")),
        ("핵심 역량 및 경험", cover.get("strengths", "")),
        ("협업 및 갈등 경험", cover.get("collaboration", "")),
        ("실패 및 학습 경험", cover.get("failure_learning", "")),
        ("입사 후 포부", cover.get("aspiration", "")),
    ]
    for title, content in sections:
        if not content:
            continue
        story.append(Paragraph(title, styles["sub"]))
        story.append(Paragraph(content, styles["body"]))
        story.append(Spacer(1, 7))

    doc.build(story)


def build_portfolio_pdf(
    data: dict[str, Any], output_path: Path, font_name: str
) -> None:
    styles = build_styles(font_name)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
    )
    portfolio = data["portfolio"]
    profile = data["candidate_profile"]
    story: list[Any] = []

    story.append(Paragraph(f"{profile.get('name', '')} 포트폴리오", styles["name"]))
    story.append(Paragraph(portfolio.get("overview", ""), styles["meta"]))
    story.append(Spacer(1, 8))

    append_section_title(story, portfolio.get("title", "주요 프로젝트"), styles)
    for item in portfolio.get("projects", []):
        story.append(Paragraph(f"<b>{item.get('name', '')}</b>", styles["sub"]))
        story.append(Paragraph(f"목표: {item.get('goal', '')}", styles["body"]))
        story.append(
            Paragraph(f"기술 스택: {' / '.join(item.get('stack', []))}", styles["body"])
        )
        story.append(Paragraph(f"기여: {item.get('contribution', '')}", styles["body"]))
        story.append(Paragraph(f"성과: {item.get('impact', '')}", styles["body"]))
        story.append(
            Paragraph(f"문제 해결: {item.get('trouble_shooting', '')}", styles["body"])
        )
        story.append(Spacer(1, 8))

    doc.build(story)


def build_career_description_pdf(
    data: dict[str, Any], output_path: Path, font_name: str
) -> None:
    styles = build_styles(font_name)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
    )
    career = data["career_description"]
    profile = data["candidate_profile"]
    story: list[Any] = []

    story.append(Paragraph(f"{profile.get('name', '')} 경력기술서", styles["name"]))
    story.append(Paragraph(career.get("summary", ""), styles["meta"]))
    story.append(Spacer(1, 8))

    append_section_title(story, "주요 경력", styles)
    for item in career.get("entries", []):
        story.append(
            Paragraph(
                f"<b>{item.get('company', '')}</b> | {item.get('period', '')}",
                styles["sub"],
            )
        )
        story.append(Paragraph(f"담당 범위: {item.get('scope', '')}", styles["body"]))
        for achievement in item.get("achievements", []):
            story.append(Paragraph(f"- {achievement}", styles["bullet"]))
        story.append(
            Paragraph(f"협업 방식: {item.get('collaboration', '')}", styles["body"])
        )
        story.append(
            Paragraph(f"주요 도구: {' / '.join(item.get('tools', []))}", styles["body"])
        )
        story.append(Spacer(1, 8))

    doc.build(story)


def build_metadata_record(
    generated: dict[str, Any],
    job_code: str,
    job_display_name: str,
    persona: PersonaSpec,
    index: int,
    files: dict[str, str],
) -> dict[str, Any]:
    profile = generated["candidate_profile"]
    return {
        "job_code": job_code,
        "job_display_name": job_display_name,
        "candidate_index": index + 1,
        "candidate_name": profile.get("name"),
        "candidate_type": persona.label,
        "candidate_type_slug": persona.slug,
        "candidate_test_intent": persona.intent,
        "hidden_signals": persona.hidden_signals,
        "summary": profile.get("summary"),
        "files": files,
    }


def main() -> None:
    print("=" * 72)
    print("HR Copilot BS - 가짜 지원자 문서 생성 시작")
    print("=" * 72)

    if not OPENAI_API_KEY:
        print("OPENAI_API_KEY가 설정되지 않았습니다.")
        print(
            "예시: set OPENAI_API_KEY=sk-... && python backend/scripts/generate_fake_applicants.py"
        )
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    font_name = register_korean_font()
    persona_lookup = build_persona_lookup()
    case_plan = build_case_plan()
    summary_records: list[dict[str, Any]] = []
    total_candidates = sum(
        (min(JOB_LIMIT, len(case_specs)) if JOB_LIMIT > 0 else len(case_specs))
        for case_specs in case_plan.values()
    )
    current = 0

    random.seed(20260423)

    for job_code, job_display_name in JOB_DISPLAY_NAMES.items():
        job_dir = OUTPUT_DIR / job_display_name
        job_dir.mkdir(parents=True, exist_ok=True)
        case_specs = case_plan[job_code]
        target_count = (
            min(JOB_LIMIT, len(case_specs)) if JOB_LIMIT > 0 else len(case_specs)
        )

        print(f"\n[{job_display_name}] {target_count}명 생성")
        for index in range(target_count):
            current += 1
            case_spec = case_specs[index]
            persona = persona_lookup[case_spec.persona_slug]
            if job_code == "AI_DEV_DATA":
                persona = PersonaSpec(
                    slug=persona.slug,
                    label=persona.label,
                    intent=persona.intent,
                    hidden_signals=persona.hidden_signals,
                    extra_documents=AI_DEV_EXTRA_DOCUMENTS.copy(),
                )
            print(
                f"  [{current}/{total_candidates}] {job_display_name} - {case_spec.title}",
                end="",
                flush=True,
            )

            try:
                prompt = build_prompt(job_display_name, persona, case_spec, index)
                generated = call_openai_json(prompt)
                profile = generated["candidate_profile"]
                name_slug = safe_slug(profile.get("name", f"candidate_{index + 1}"))
                base_name = f"{job_display_name}_{index + 1:02d}_{name_slug}"

                files: dict[str, str] = {}

                bundle_path = job_dir / f"{base_name}_bundle.pdf"
                build_resume_bundle_pdf(generated, bundle_path, font_name)
                files["resume_bundle_pdf"] = str(bundle_path.resolve())

                if generated.get("portfolio", {}).get("required"):
                    portfolio_path = job_dir / f"{base_name}_portfolio.pdf"
                    build_portfolio_pdf(generated, portfolio_path, font_name)
                    files["portfolio_pdf"] = str(portfolio_path.resolve())

                if generated.get("career_description", {}).get("required"):
                    career_path = job_dir / f"{base_name}_career_description.pdf"
                    build_career_description_pdf(generated, career_path, font_name)
                    files["career_description_pdf"] = str(career_path.resolve())

                raw_json_path = job_dir / f"{base_name}_source.json"
                write_json(raw_json_path, generated)
                files["source_json"] = str(raw_json_path.resolve())

                metadata = build_metadata_record(
                    generated=generated,
                    job_code=job_code,
                    job_display_name=job_display_name,
                    persona=persona,
                    index=index,
                    files=files,
                )
                metadata["candidate_case_code"] = case_spec.code
                metadata["candidate_case_title"] = case_spec.title
                metadata["candidate_case_description"] = case_spec.description
                metadata["candidate_case_must_haves"] = case_spec.must_haves
                metadata_path = job_dir / f"{base_name}_meta.json"
                write_json(metadata_path, metadata)
                files["meta_json"] = str(metadata_path.resolve())
                summary_records.append(metadata)
                write_json(OUTPUT_DIR / "_summary.json", summary_records)

                print(f" 완료 - {profile.get('name', '')}")
                time.sleep(DELAY_SECONDS)
            except KeyboardInterrupt:
                print("\n중단 요청을 받아 생성 작업을 종료합니다.")
                summary_path = OUTPUT_DIR / "_summary.json"
                write_json(summary_path, summary_records)
                print(f"중간 저장된 요약 파일: {summary_path.resolve()}")
                return
            except Exception as exc:
                print(f" 실패 - {exc}")

    summary_path = OUTPUT_DIR / "_summary.json"
    write_json(summary_path, summary_records)

    print("\n" + "=" * 72)
    print(f"완료: 총 {len(summary_records)}명 생성")
    print(f"출력 폴더: {OUTPUT_DIR.resolve()}")
    print(f"요약 파일: {summary_path.resolve()}")
    print("지원자 유형은 PDF 본문이 아니라 meta/summary JSON에 기록됩니다.")
    print("=" * 72)


if __name__ == "__main__":
    main()
