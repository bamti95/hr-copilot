from openai import AsyncOpenAI

from core.config import settings


def get_openai_model() -> str:
    return getattr(settings, "OPENAI_MODEL", None) or "gpt-4.1-mini"


client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
