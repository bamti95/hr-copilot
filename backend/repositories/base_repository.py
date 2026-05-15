"""리포지토리 공통 베이스 클래스.

여러 도메인 리포지토리가 공통으로 쓰는 최소한의 DB 작업만 모아 둔다.
도메인별 조회 조건과 집계 로직은 하위 리포지토리에서 구현한다.
"""

from typing import Generic, TypeVar, Type, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")

class BaseRepository(Generic[ModelT]):
    """공통 CRUD 보조 기능을 제공하는 베이스 리포지토리."""

    def __init__(self, db: AsyncSession, model: Type[ModelT]):
        self.db = db
        self.model = model

    async def add(self, entity: ModelT) -> ModelT:
        """엔터티를 세션에 올린다.

        커밋은 호출자가 트랜잭션 단위에서 직접 처리한다.
        """
        self.db.add(entity)
        return entity

    async def flush(self) -> None:
        """DB에 반영할 SQL을 즉시 밀어 넣어 PK 같은 값을 확보한다."""
        await self.db.flush()

    async def refresh(self, entity: ModelT) -> None:
        """DB 기준 최신 상태로 엔터티를 다시 읽는다."""
        await self.db.refresh(entity)

    async def get_by_id(self, entity_id: int) -> Optional[ModelT]:
        """기본 PK 조회를 수행한다."""
        stmt = select(self.model).where(self.model.id == entity_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
