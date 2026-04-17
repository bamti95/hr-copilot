from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import get_settings
from models import Candidate, Document, InterviewQuestion, InterviewSession, LlmCallLog, Manager, PromptProfile
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
        await conn.run_sync(Base.metadata.create_all)
        # 기존 DB는 create_all이 스키마를 바꾸지 않으므로, 모델에만 추가된 컬럼을 여기서 보강합니다.
        await conn.execute(
            text(
                "ALTER TABLE candidate ADD COLUMN IF NOT EXISTS updated_at "
                "TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()"
            )
        )
