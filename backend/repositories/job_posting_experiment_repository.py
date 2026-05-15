from __future__ import annotations

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.job_posting_experiment_case_result import JobPostingExperimentCaseResult
from models.job_posting_experiment_run import JobPostingExperimentRun
from repositories.base_repository import BaseRepository


class JobPostingExperimentRunRepository(BaseRepository[JobPostingExperimentRun]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, JobPostingExperimentRun)

    async def find_by_id_not_deleted(self, run_id: int) -> JobPostingExperimentRun | None:
        stmt = select(JobPostingExperimentRun).where(
            JobPostingExperimentRun.id == run_id,
            JobPostingExperimentRun.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def count_list(self) -> int:
        stmt = select(func.count()).select_from(JobPostingExperimentRun).where(
            JobPostingExperimentRun.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        return int(result.scalar_one() or 0)

    async def find_list(self, *, page: int, size: int) -> list[JobPostingExperimentRun]:
        stmt = (
            select(JobPostingExperimentRun)
            .where(JobPostingExperimentRun.deleted_at.is_(None))
            .order_by(desc(JobPostingExperimentRun.created_at), desc(JobPostingExperimentRun.id))
            .offset(page * size)
            .limit(size)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class JobPostingExperimentCaseResultRepository(BaseRepository[JobPostingExperimentCaseResult]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, JobPostingExperimentCaseResult)

    async def find_by_run_id(
        self,
        run_id: int,
        *,
        limit: int | None = None,
    ) -> list[JobPostingExperimentCaseResult]:
        stmt = (
            select(JobPostingExperimentCaseResult)
            .where(
                JobPostingExperimentCaseResult.experiment_run_id == run_id,
                JobPostingExperimentCaseResult.deleted_at.is_(None),
            )
            .order_by(
                JobPostingExperimentCaseResult.case_index.asc(),
                JobPostingExperimentCaseResult.id.asc(),
            )
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
