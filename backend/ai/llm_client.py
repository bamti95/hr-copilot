from openai import AsyncOpenAI

from core.config import settings


def get_openai_model() -> str:
    return getattr(settings, "OPENAI_MODEL", None) or "gpt-5-mini"

client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    timeout=settings.OPENAI_TIMEOUT_SECONDS,
)
