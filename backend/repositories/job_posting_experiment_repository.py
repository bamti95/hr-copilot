"""채용공고 실험 실행 결과 조회 리포지토리.

실험 run과 케이스 결과를 관리 화면과 실험 비교 기능에서 읽을 때 사용한다.
실험 요약과 케이스 상세를 분리해 조회하는 것이 핵심 역할이다.
"""

from __future__ import annotations

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.job_posting_experiment_case_result import JobPostingExperimentCaseResult
from models.job_posting_experiment_run import JobPostingExperimentRun
from repositories.base_repository import BaseRepository


class JobPostingExperimentRunRepository(BaseRepository[JobPostingExperimentRun]):
    """실험 run 상위 엔터티 조회를 담당한다."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, JobPostingExperimentRun)

    async def find_by_id_not_deleted(self, run_id: int) -> JobPostingExperimentRun | None:
        """삭제되지 않은 실험 run 1건을 조회한다."""
        stmt = select(JobPostingExperimentRun).where(
            JobPostingExperimentRun.id == run_id,
            JobPostingExperimentRun.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def count_list(self) -> int:
        """실험 run 총개수를 센다."""
        stmt = select(func.count()).select_from(JobPostingExperimentRun).where(
            JobPostingExperimentRun.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        return int(result.scalar_one() or 0)

    async def find_list(self, *, page: int, size: int) -> list[JobPostingExperimentRun]:
        """실험 run 목록을 최신순으로 페이지 조회한다."""
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
    """실험 케이스 결과 상세 조회를 담당한다."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, JobPostingExperimentCaseResult)

    async def find_by_run_id(
        self,
        run_id: int,
        *,
        limit: int | None = None,
    ) -> list[JobPostingExperimentCaseResult]:
        """실험 run 1건에 속한 케이스 결과를 순서대로 조회한다."""
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
