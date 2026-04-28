import os

from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "y", "yes", "on"}


class Settings:
    DB_HOST: str = os.getenv("DB_HOST", "")
    DB_PORT: int = int(os.getenv("DB_PORT", 5432))
    DB_NAME: str = os.getenv("DB_NAME", "")
    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_ECHO: bool = _parse_bool(os.getenv("DB_ECHO"), True)

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 60)
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(
        os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 14)
    )

    PASSWORD_BCRYPT_ROUNDS: int = int(
        os.getenv("PASSWORD_BCRYPT_ROUNDS", 12)
    )

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    OPENAI_TIMEOUT_SECONDS: float = float(os.getenv("OPENAI_TIMEOUT_SECONDS", 180))
    QUESTION_GENERATION_JOB_TIMEOUT_SECONDS: float = float(
        os.getenv("QUESTION_GENERATION_JOB_TIMEOUT_SECONDS", 900)
    )
    QUESTION_GENERATION_STALE_SECONDS: float = float(
        os.getenv("QUESTION_GENERATION_STALE_SECONDS", 1800)
    )
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv(
        "CELERY_RESULT_BACKEND",
        "redis://localhost:6379/1",
    )
    CELERY_TASK_DEFAULT_QUEUE: str = os.getenv(
        "CELERY_TASK_DEFAULT_QUEUE",
        "question-generation",
    )
    CELERY_WORKER_CONCURRENCY: int = int(os.getenv("CELERY_WORKER_CONCURRENCY", 5))
    UPLOAD_PATH: str = os.getenv("UPLOAD_PATH")

    @property
    def DATABASE_URL(self) -> str:
        user = quote_plus(self.DB_USER)
        password = quote_plus(self.DB_PASSWORD)
        return (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
        
settings = Settings()


def get_settings():
    return settings
