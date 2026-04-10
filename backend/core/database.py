from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import get_settings

from models.base import Base # 모든 모델이 정의된 Base 클래스 임포트

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    future=True,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
        
async def init_db():
    async with engine.begin() as conn:
        # 모델에 정의된 내용을 바탕으로 테이블 자동 생성 (Auto DDL)
        await conn.run_sync(Base.metadata.create_all)        
        
        