from openai import AsyncOpenAI

from core.config import DEFAULT_OPENAI_MODEL, settings


def get_openai_model() -> str:
    return getattr(settings, "OPENAI_MODEL", None) or DEFAULT_OPENAI_MODEL

client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    timeout=settings.OPENAI_TIMEOUT_SECONDS,
)
