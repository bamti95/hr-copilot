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
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        # Schema changes are managed by Alembic migrations.
        # Keep startup lightweight and fail fast if the database is unreachable.
        await conn.execute(text("SELECT 1"))
