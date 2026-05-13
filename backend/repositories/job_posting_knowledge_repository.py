from __future__ import annotations

from sqlalchemy import String, desc, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.job_posting_knowledge_chunk import JobPostingKnowledgeChunk
from models.job_posting_knowledge_source import JobPostingKnowledgeSource
from repositories.base_repository import BaseRepository


class JobPostingKnowledgeSourceRepository(BaseRepository[JobPostingKnowledgeSource]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, JobPostingKnowledgeSource)

    async def find_by_id_not_deleted(
        self,
        source_id: int,
    ) -> JobPostingKnowledgeSource | None:
        stmt = select(JobPostingKnowledgeSource).where(
            JobPostingKnowledgeSource.id == source_id,
            JobPostingKnowledgeSource.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_file_path(
        self,
        file_path: str,
    ) -> JobPostingKnowledgeSource | None:
        stmt = select(JobPostingKnowledgeSource).where(
            JobPostingKnowledgeSource.file_path == file_path,
            JobPostingKnowledgeSource.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def count_list(
        self,
        *,
        source_type: str | None = None,
        keyword: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(JobPostingKnowledgeSource).where(
            JobPostingKnowledgeSource.deleted_at.is_(None)
        )
        if source_type:
            stmt = stmt.where(JobPostingKnowledgeSource.source_type == source_type)
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(
                JobPostingKnowledgeSource.title.ilike(like)
                | JobPostingKnowledgeSource.source_name.ilike(like)
            )
        result = await self.db.execute(stmt)
        return int(result.scalar_one() or 0)

    async def find_list(
        self,
        *,
        page: int,
        size: int,
        source_type: str | None = None,
        keyword: str | None = None,
    ) -> list[JobPostingKnowledgeSource]:
        stmt = select(JobPostingKnowledgeSource).where(
            JobPostingKnowledgeSource.deleted_at.is_(None)
        )
        if source_type:
            stmt = stmt.where(JobPostingKnowledgeSource.source_type == source_type)
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(
                JobPostingKnowledgeSource.title.ilike(like)
                | JobPostingKnowledgeSource.source_name.ilike(like)
            )
        stmt = stmt.order_by(desc(JobPostingKnowledgeSource.created_at)).offset(page * size).limit(size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class JobPostingKnowledgeChunkRepository(BaseRepository[JobPostingKnowledgeChunk]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, JobPostingKnowledgeChunk)

    async def delete_by_source_id(self, source_id: int) -> None:
        chunks = await self.find_by_source_id(source_id, limit=100000)
        for chunk in chunks:
            await self.db.delete(chunk)

    async def find_by_source_id(
        self,
        source_id: int,
        *,
        limit: int = 100,
    ) -> list[JobPostingKnowledgeChunk]:
        stmt = (
            select(JobPostingKnowledgeChunk)
            .where(
                JobPostingKnowledgeChunk.knowledge_source_id == source_id,
                JobPostingKnowledgeChunk.del_tf == "N",
            )
            .order_by(JobPostingKnowledgeChunk.chunk_index)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def search_candidates(
        self,
        *,
        query_terms: list[str],
        limit: int = 30,
    ) -> list[JobPostingKnowledgeChunk]:
        stmt = (
            select(JobPostingKnowledgeChunk)
            .options(selectinload(JobPostingKnowledgeChunk.knowledge_source))
            .where(
                JobPostingKnowledgeChunk.use_tf == "Y",
                JobPostingKnowledgeChunk.del_tf == "N",
            )
        )
        if query_terms:
            conditions = [
                JobPostingKnowledgeChunk.content.ilike(f"%{term}%")
                | JobPostingKnowledgeChunk.summary.ilike(f"%{term}%")
                | JobPostingKnowledgeChunk.issue_code.ilike(f"%{term}%")
                | JobPostingKnowledgeChunk.law_name.ilike(f"%{term}%")
                for term in query_terms
                if term
            ]
            if conditions:
                condition = conditions[0]
                for item in conditions[1:]:
                    condition = condition | item
                stmt = stmt.where(condition)
        stmt = stmt.order_by(desc(JobPostingKnowledgeChunk.created_at)).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def search_by_full_text(
        self,
        *,
        query: str,
        query_terms: list[str],
        limit: int = 30,
    ) -> list[tuple[JobPostingKnowledgeChunk, float]]:
        vector = func.to_tsvector(
            "simple",
            func.concat_ws(
                " ",
                JobPostingKnowledgeChunk.content,
                JobPostingKnowledgeChunk.summary,
                JobPostingKnowledgeChunk.issue_code,
                JobPostingKnowledgeChunk.law_name,
                JobPostingKnowledgeChunk.article_no,
                JobPostingKnowledgeChunk.tags.cast(String),
            ),
        )
        ts_query = func.websearch_to_tsquery("simple", query)
        rank = func.ts_rank_cd(vector, ts_query)
        conditions = [vector.op("@@")(ts_query)]
        if query_terms:
            keyword_conditions = [
                JobPostingKnowledgeChunk.content.ilike(f"%{term}%")
                | JobPostingKnowledgeChunk.summary.ilike(f"%{term}%")
                | JobPostingKnowledgeChunk.issue_code.ilike(f"%{term}%")
                | JobPostingKnowledgeChunk.law_name.ilike(f"%{term}%")
                | JobPostingKnowledgeChunk.tags.cast(String).ilike(f"%{term}%")
                for term in query_terms
                if term
            ]
            if keyword_conditions:
                conditions.append(or_(*keyword_conditions))

        stmt = (
            select(JobPostingKnowledgeChunk, rank.label("text_score"))
            .options(selectinload(JobPostingKnowledgeChunk.knowledge_source))
            .where(
                JobPostingKnowledgeChunk.use_tf == "Y",
                JobPostingKnowledgeChunk.del_tf == "N",
                or_(*conditions),
            )
            .order_by(desc(rank), desc(JobPostingKnowledgeChunk.created_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        return [(chunk, float(score or 0.0)) for chunk, score in rows]

    async def search_by_vector(
        self,
        *,
        query_embedding: list[float],
        limit: int = 30,
    ) -> list[tuple[JobPostingKnowledgeChunk, float]]:
        if not query_embedding:
            return []
        distance = JobPostingKnowledgeChunk.embedding.cosine_distance(query_embedding)
        stmt = (
            select(JobPostingKnowledgeChunk, (literal(1.0) - distance).label("vector_score"))
            .options(selectinload(JobPostingKnowledgeChunk.knowledge_source))
            .where(
                JobPostingKnowledgeChunk.use_tf == "Y",
                JobPostingKnowledgeChunk.del_tf == "N",
                JobPostingKnowledgeChunk.embedding.is_not(None),
            )
            .order_by(distance.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        return [(chunk, float(score or 0.0)) for chunk, score in rows]

    async def find_search_pool(
        self,
        *,
        query_terms: list[str],
        limit: int = 500,
    ) -> list[JobPostingKnowledgeChunk]:
        stmt = (
            select(JobPostingKnowledgeChunk)
            .options(selectinload(JobPostingKnowledgeChunk.knowledge_source))
            .where(
                JobPostingKnowledgeChunk.use_tf == "Y",
                JobPostingKnowledgeChunk.del_tf == "N",
            )
        )
        if query_terms:
            conditions = [
                JobPostingKnowledgeChunk.content.ilike(f"%{term}%")
                | JobPostingKnowledgeChunk.summary.ilike(f"%{term}%")
                | JobPostingKnowledgeChunk.issue_code.ilike(f"%{term}%")
                | JobPostingKnowledgeChunk.law_name.ilike(f"%{term}%")
                | JobPostingKnowledgeChunk.tags.cast(String).ilike(f"%{term}%")
                for term in query_terms
                if term
            ]
            if conditions:
                condition = conditions[0]
                for item in conditions[1:]:
                    condition = condition | item
                stmt = stmt.where(condition)
        stmt = stmt.order_by(desc(JobPostingKnowledgeChunk.created_at)).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
