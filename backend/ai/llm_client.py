"""OpenAI 비동기 클라이언트와 기본 모델 선택 함수를 제공한다."""

from openai import AsyncOpenAI

from core.config import DEFAULT_OPENAI_MODEL, settings


def get_openai_model() -> str:
    """환경 설정에 맞는 기본 OpenAI 모델 이름을 반환한다."""
    return getattr(settings, "OPENAI_MODEL", None) or DEFAULT_OPENAI_MODEL

client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    timeout=settings.OPENAI_TIMEOUT_SECONDS,
)
