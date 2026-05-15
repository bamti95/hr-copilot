"""채용공고 분석용 지식 저장소 조회 로직.

법령, 가이드, 사례 chunk를 검색 목적에 맞게 조회한다.
무거운 `ILIKE` 조건은 줄이고, issue code 같은 구조화 필드를 우선 활용하는 것이 핵심 규칙이다.
"""

from __future__ import annotations

from sqlalchemy import desc, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.job_posting_knowledge_chunk import JobPostingKnowledgeChunk
from models.job_posting_knowledge_source import JobPostingKnowledgeSource
from repositories.base_repository import BaseRepository


# fallback 키워드는 많이 붙일수록 DB 조건이 급격히 커져 상한을 둔다.
MAX_KEYWORD_TERMS = 5
KEYWORD_STOPWORDS = {
    "채용공고",
    "공정채용",
    "기준",
    "없이",
    "제시되어",
    "낮습니다",
    "구체적",
    "추상적으로",
    "기회가",
    "복지나",
    "the",
    "and",
    "or",
    "for",
    "with",
}
# issue code는 문자열 검색보다 exact match가 훨씬 안정적이라 별도 사전을 둔다.
KNOWN_ISSUE_CODES = {
    "age_discrimination": "AGE_DISCRIMINATION",
    "benefit_vague": "BENEFIT_VAGUE",
    "culture_red_flag": "CULTURE_RED_FLAG",
    "false_job_ad": "FALSE_JOB_AD",
    "gender_discrimination": "GENDER_DISCRIMINATION",
    "irrelevant_personal_info": "IRRELEVANT_PERSONAL_INFO",
    "job_description_vague": "JOB_DESCRIPTION_VAGUE",
    "overtime_risk": "OVERTIME_RISK",
    "physical_condition": "PHYSICAL_CONDITION",
    "repeated_posting": "REPEATED_POSTING",
    "salary_missing": "SALARY_MISSING",
    "unfavorable_condition_change": "UNFAVORABLE_CONDITION_CHANGE",
    "working_condition_ambiguity": "WORKING_CONDITION_AMBIGUITY",
}


def normalize_keyword_terms(query_terms: list[str]) -> list[str]:
    """fallback 검색에 쓸 핵심 토큰만 남긴다.

    짧은 토큰, 불용어, issue code 자체는 제거한다.
    결과 개수는 `MAX_KEYWORD_TERMS` 이내로 제한한다.
    """
    normalized: list[str] = []
    for term in query_terms:
        value = (term or "").strip().lower()
        if len(value) < 2:
            continue
        if value in KEYWORD_STOPWORDS:
            continue
        if value in KNOWN_ISSUE_CODES:
            continue
        if value not in normalized:
            normalized.append(value)
        if len(normalized) >= MAX_KEYWORD_TERMS:
            break
    return normalized


def extract_issue_codes(query_terms: list[str]) -> list[str]:
    """질의 토큰 안의 issue code를 추출한다."""
    codes: list[str] = []
    for term in query_terms:
        code = KNOWN_ISSUE_CODES.get((term or "").strip().lower())
        if code and code not in codes:
            codes.append(code)
    return codes


class JobPostingKnowledgeSourceRepository(BaseRepository[JobPostingKnowledgeSource]):
    """지식 원본 문서 메타데이터를 조회하는 저장소."""

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
    """RAG 검색에 쓰이는 chunk 조회 저장소.

    검색 경로는 metadata exact, full-text, keyword fallback, vector로 나뉜다.
    각 경로는 비용과 정확도 성격이 달라 서비스 계층에서 조합해 쓴다.
    """

    def __init__(self, db: AsyncSession):
        super().__init__(db, JobPostingKnowledgeChunk)

    async def delete_by_source_id(self, source_id: int) -> None:
        """원본 문서 삭제 시 연결된 chunk도 함께 지운다."""
        chunks = await self.find_by_source_id(source_id, limit=100000)
        for chunk in chunks:
            await self.db.delete(chunk)

    async def find_by_source_id(
        self,
        source_id: int,
        *,
        limit: int = 100,
    ) -> list[JobPostingKnowledgeChunk]:
        """원본 문서에 속한 chunk를 순서대로 조회한다."""
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
        """관리성 후보 조회용 간단 검색이다.

        summary와 law_name 중심으로만 찾는다.
        긴 본문 검색은 제외해 관리 화면 조회 비용을 낮춘다.
        """
        stmt = (
            select(JobPostingKnowledgeChunk)
            .options(selectinload(JobPostingKnowledgeChunk.knowledge_source))
            .where(
                JobPostingKnowledgeChunk.use_tf == "Y",
                JobPostingKnowledgeChunk.del_tf == "N",
            )
        )
        if query_terms:
            keyword_terms = normalize_keyword_terms(query_terms)
            issue_codes = extract_issue_codes(query_terms)
            conditions = []
            if issue_codes:
                conditions.append(JobPostingKnowledgeChunk.issue_code.in_(issue_codes))
            conditions.extend(
                JobPostingKnowledgeChunk.summary.ilike(f"%{term}%")
                | JobPostingKnowledgeChunk.law_name.ilike(f"%{term}%")
                for term in keyword_terms
            )
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
        """PostgreSQL full-text 검색을 수행한다.

        본문, 요약, issue_code, 법령명을 하나의 tsvector로 묶어 순위를 계산한다.
        issue code가 질의에 포함되면 exact match 조건을 함께 붙인다.
        """
        vector = func.to_tsvector(
            "simple",
            func.concat_ws(
                " ",
                JobPostingKnowledgeChunk.content,
                JobPostingKnowledgeChunk.summary,
                JobPostingKnowledgeChunk.issue_code,
                JobPostingKnowledgeChunk.law_name,
                JobPostingKnowledgeChunk.article_no,
            ),
        )
        ts_query = func.websearch_to_tsquery("simple", query)
        rank = func.ts_rank_cd(vector, ts_query)
        conditions = [vector.op("@@")(ts_query)]
        issue_codes = extract_issue_codes(query_terms)
        if issue_codes:
            conditions.append(JobPostingKnowledgeChunk.issue_code.in_(issue_codes))

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

    async def search_by_keyword_fallback(
        self,
        *,
        query_terms: list[str],
        limit: int = 30,
    ) -> list[tuple[JobPostingKnowledgeChunk, float]]:
        """full-text가 약할 때만 쓰는 가벼운 fallback 검색이다.

        summary와 law_name에만 제한적으로 `ILIKE`를 건다.
        점수는 낮은 기본값 0.01로 두어 본 검색보다 뒤에 오도록 한다.
        """
        keyword_terms = normalize_keyword_terms(query_terms)
        issue_codes = extract_issue_codes(query_terms)
        conditions = []
        if issue_codes:
            conditions.append(JobPostingKnowledgeChunk.issue_code.in_(issue_codes))
        conditions.extend(
            JobPostingKnowledgeChunk.summary.ilike(f"%{term}%")
            | JobPostingKnowledgeChunk.law_name.ilike(f"%{term}%")
            for term in keyword_terms
        )
        if not conditions:
            return []

        stmt = (
            select(JobPostingKnowledgeChunk, literal(0.01).label("text_score"))
            .options(selectinload(JobPostingKnowledgeChunk.knowledge_source))
            .where(
                JobPostingKnowledgeChunk.use_tf == "Y",
                JobPostingKnowledgeChunk.del_tf == "N",
                or_(*conditions),
            )
            .order_by(desc(JobPostingKnowledgeChunk.created_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        return [(chunk, float(score or 0.0)) for chunk, score in rows]

    async def search_by_metadata_exact(
        self,
        *,
        issue_type: str | None,
        query_terms: list[str],
        limit: int = 30,
    ) -> list[tuple[JobPostingKnowledgeChunk, float]]:
        """구조화 필드 중심의 빠른 검색이다.

        issue_code, risk_category, law_name처럼 인지하기 쉬운 슬롯을 먼저 확인한다.
        Hybrid Lite 전략에서 가장 먼저 실행되는 경로다.
        """
        issue_codes = extract_issue_codes(query_terms)
        if issue_type and issue_type not in issue_codes:
            issue_codes.append(issue_type)

        keyword_terms = normalize_keyword_terms(query_terms)
        conditions = []
        if issue_codes:
            conditions.append(JobPostingKnowledgeChunk.issue_code.in_(issue_codes))
            conditions.append(JobPostingKnowledgeChunk.risk_category.in_(issue_codes))
        # law_name은 부분 일치가 유용하지만 비용을 줄이기 위해 상위 3개 토큰만 허용한다.
        conditions.extend(JobPostingKnowledgeChunk.law_name.ilike(f"%{term}%") for term in keyword_terms[:3])
        if not conditions:
            return []

        stmt = (
            select(JobPostingKnowledgeChunk, literal(0.2).label("metadata_score"))
            .options(selectinload(JobPostingKnowledgeChunk.knowledge_source))
            .where(
                JobPostingKnowledgeChunk.use_tf == "Y",
                JobPostingKnowledgeChunk.del_tf == "N",
                or_(*conditions),
            )
            .order_by(desc(JobPostingKnowledgeChunk.created_at))
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
        """pgvector 코사인 거리로 의미 유사 chunk를 찾는다."""
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
        """파이썬 벡터 fallback용 검색 풀을 좁혀 가져온다.

        DB에서 먼저 대략적인 후보군을 줄인 뒤 메모리에서 코사인 유사도를 계산한다.
        전체 테이블을 직접 순회하지 않게 하려는 의도다.
        """
        stmt = (
            select(JobPostingKnowledgeChunk)
            .options(selectinload(JobPostingKnowledgeChunk.knowledge_source))
            .where(
                JobPostingKnowledgeChunk.use_tf == "Y",
                JobPostingKnowledgeChunk.del_tf == "N",
            )
        )
        if query_terms:
            keyword_terms = normalize_keyword_terms(query_terms)
            issue_codes = extract_issue_codes(query_terms)
            conditions = []
            if issue_codes:
                conditions.append(JobPostingKnowledgeChunk.issue_code.in_(issue_codes))
            conditions.extend(
                JobPostingKnowledgeChunk.summary.ilike(f"%{term}%")
                | JobPostingKnowledgeChunk.law_name.ilike(f"%{term}%")
                for term in keyword_terms
            )
            if conditions:
                condition = conditions[0]
                for item in conditions[1:]:
                    condition = condition | item
                stmt = stmt.where(condition)
        stmt = stmt.order_by(desc(JobPostingKnowledgeChunk.created_at)).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
