from typing import Generic, TypeVar, Type, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")

class BaseRepository(Generic[ModelT]):
    def __init__(self, db: AsyncSession, model: Type[ModelT]):
        self.db = db
        self.model = model

    async def add(self, entity: ModelT) -> ModelT:
        self.db.add(entity)
        return entity

    async def flush(self) -> None:
        await self.db.flush()

    async def refresh(self, entity: ModelT) -> None:
        await self.db.refresh(entity)

    async def get_by_id(self, entity_id: int) -> Optional[ModelT]:
        stmt = select(self.model).where(self.model.id == entity_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()