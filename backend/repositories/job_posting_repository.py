"""채용공고와 분석 리포트 조회 리포지토리.

공고 본문과 분석 결과를 관리 화면에서 조회할 때 쓰는 기본 검색을 제공한다.
채용공고 분석 서비스가 중복 공고를 식별할 때도 이 저장소를 사용한다.
"""

from __future__ import annotations

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.job_posting import JobPosting
from models.job_posting_analysis_report import JobPostingAnalysisReport
from repositories.base_repository import BaseRepository


class JobPostingRepository(BaseRepository[JobPosting]):
    """채용공고 엔터티 조회를 담당한다."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, JobPosting)

    async def find_by_id_not_deleted(self, posting_id: int) -> JobPosting | None:
        """삭제되지 않은 공고 1건을 조회한다."""
        stmt = select(JobPosting).where(
            JobPosting.id == posting_id,
            JobPosting.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_hash(self, posting_text_hash: str) -> JobPosting | None:
        """본문 해시로 중복 공고를 찾는다."""
        stmt = select(JobPosting).where(
            JobPosting.posting_text_hash == posting_text_hash,
            JobPosting.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def count_list(self, *, keyword: str | None = None) -> int:
        """검색 조건에 맞는 공고 수를 센다."""
        stmt = select(func.count()).select_from(JobPosting).where(
            JobPosting.deleted_at.is_(None)
        )
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(
                JobPosting.job_title.ilike(like)
                | JobPosting.company_name.ilike(like)
                | JobPosting.posting_text.ilike(like)
            )
        result = await self.db.execute(stmt)
        return int(result.scalar_one() or 0)

    async def find_list(
        self,
        *,
        page: int,
        size: int,
        keyword: str | None = None,
    ) -> list[JobPosting]:
        """공고 목록을 최신순으로 조회한다."""
        stmt = select(JobPosting).where(JobPosting.deleted_at.is_(None))
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(
                JobPosting.job_title.ilike(like)
                | JobPosting.company_name.ilike(like)
                | JobPosting.posting_text.ilike(like)
            )
        stmt = stmt.order_by(desc(JobPosting.created_at)).offset(page * size).limit(size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class JobPostingAnalysisReportRepository(BaseRepository[JobPostingAnalysisReport]):
    """채용공고 분석 리포트 조회를 담당한다."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, JobPostingAnalysisReport)

    async def find_by_id_not_deleted(
        self,
        report_id: int,
    ) -> JobPostingAnalysisReport | None:
        """삭제되지 않은 분석 리포트 1건을 조회한다."""
        stmt = select(JobPostingAnalysisReport).where(
            JobPostingAnalysisReport.id == report_id,
            JobPostingAnalysisReport.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_posting_id(
        self,
        posting_id: int,
        *,
        limit: int = 20,
    ) -> list[JobPostingAnalysisReport]:
        """공고 1건에 연결된 리포트를 최신순으로 가져온다."""
        stmt = (
            select(JobPostingAnalysisReport)
            .where(
                JobPostingAnalysisReport.job_posting_id == posting_id,
                JobPostingAnalysisReport.deleted_at.is_(None),
            )
            .order_by(desc(JobPostingAnalysisReport.created_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
