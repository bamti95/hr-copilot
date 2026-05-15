"""비동기 DB 엔진과 세션 팩토리를 구성한다.

의존성 주입용 세션과 시작 시점 연결 확인 함수를 함께 제공한다.
"""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import get_settings
from models import (
    AiJob,
    Candidate,
    Document,
    InterviewQuestion,
    InterviewSession,
    JobPosting,
    JobPostingAnalysisReport,
    JobPostingExperimentCaseResult,
    JobPostingExperimentRun,
    JobPostingKnowledgeChunk,
    JobPostingKnowledgeSource,
    LlmCallLog,
    Manager,
    PromptProfile,
)
from models.base import Base

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    future=True,
    pool_pre_ping=True,
    echo=settings.DB_ECHO,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """요청 단위 비동기 DB 세션을 제공한다."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """애플리케이션 시작 시 DB 연결 가능 여부만 확인한다."""
    async with engine.begin() as conn:
        # Schema changes are managed by Alembic migrations.
        # Keep startup lightweight and fail fast if the database is unreachable.
        await conn.execute(text("SELECT 1"))
