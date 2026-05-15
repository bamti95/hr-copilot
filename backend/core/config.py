"""환경 변수 기반 애플리케이션 설정을 관리한다.

백엔드 전역에서 공통으로 쓰는 DB, 인증, OpenAI 관련 설정을 모은다.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from urllib.parse import quote_plus

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OPENAI_MODEL = "gpt-5-mini"

load_dotenv(BASE_DIR / ".env")

def _parse_bool(value: str | None, default: bool = False) -> bool:
    """문자열 환경 변수를 bool 값으로 해석한다."""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "y", "yes", "on"}


class Settings:
    """애플리케이션 전역 설정 객체다."""

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
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip() or DEFAULT_OPENAI_MODEL
    OPENAI_TIMEOUT_SECONDS: float = float(os.getenv("OPENAI_TIMEOUT_SECONDS", 360))
    QUESTION_GENERATION_JOB_TIMEOUT_SECONDS: float = float(
        os.getenv("QUESTION_GENERATION_JOB_TIMEOUT_SECONDS", 900)
    )
    QUESTION_GENERATION_STALE_SECONDS: float = float(
        os.getenv("QUESTION_GENERATION_STALE_SECONDS", 1800)
    )
    UPLOAD_PATH: str = os.getenv("UPLOAD_PATH")
    
    # ==============================
    # LANGSMITH 추가
    # ==============================
    LANGCHAIN_TRACING_V2: bool = _parse_bool(
        os.getenv("LANGCHAIN_TRACING_V2"), True
    )
    
    # API 키 (LangSmith 설정 페이지에서 발급)
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")

    # 프로젝트 이름 (LangSmith 대시보드에서 구분할 이름)
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "HR-Copilot")
    
    # (선택) 엔드포인트
    LANGCHAIN_ENDPOINT: str = os.getenv(
        "LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"
    )
    
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
    """싱글턴 설정 객체를 반환한다."""
    return settings
