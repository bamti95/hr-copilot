from __future__ import annotations

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.job_posting import JobPosting
from models.job_posting_analysis_report import JobPostingAnalysisReport
from repositories.base_repository import BaseRepository


class JobPostingRepository(BaseRepository[JobPosting]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, JobPosting)

    async def find_by_id_not_deleted(self, posting_id: int) -> JobPosting | None:
        stmt = select(JobPosting).where(
            JobPosting.id == posting_id,
            JobPosting.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_hash(self, posting_text_hash: str) -> JobPosting | None:
        stmt = select(JobPosting).where(
            JobPosting.posting_text_hash == posting_text_hash,
            JobPosting.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def count_list(self, *, keyword: str | None = None) -> int:
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
    def __init__(self, db: AsyncSession):
        super().__init__(db, JobPostingAnalysisReport)

    async def find_by_id_not_deleted(
        self,
        report_id: int,
    ) -> JobPostingAnalysisReport | None:
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
