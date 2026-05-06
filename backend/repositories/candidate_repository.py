from sqlalchemy import distinct, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.manager import Manager
from models.interview_session import InterviewSession
from models.candidate import Candidate
from models.document import Document
from repositories.base_repository import BaseRepository


def _candidate_phone_digits_expr():
    """PostgreSQL: digits-only form of candidate.phone for duplicate checks."""
    return func.regexp_replace(Candidate.phone, "[^0-9]", "", "g")


class CandidateRepository(BaseRepository[Candidate]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Candidate)

    async def find_by_id_not_deleted(self, candidate_id: int) -> Candidate | None:
        stmt = (
            select(Candidate, Manager.name.label("created_name"))
            .outerjoin(Manager, Candidate.created_by == Manager.id)
            .where(
                Candidate.id == candidate_id,
                Candidate.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        row = result.one_or_none()
        if row is None:
            return None
        candidate, created_name = row
        setattr(candidate, "created_name", created_name)
        return candidate

    async def find_by_id_any(self, candidate_id: int) -> Candidate | None:
        stmt = select(Candidate).where(Candidate.id == candidate_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_active_documents_by_candidate_id(self, candidate_id: int) -> list[Document]:
        stmt = (
            select(Document)
            .where(
                Document.candidate_id == candidate_id,
                Document.deleted_at.is_(None),
            )
            .order_by(Document.id.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def find_active_document_by_id(
        self,
        candidate_id: int,
        document_id: int,
    ) -> Document | None:
        stmt = select(Document).where(
            Document.id == document_id,
            Document.candidate_id == candidate_id,
            Document.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_document_by_id_any(self, document_id: int) -> Document | None:
        stmt = select(Document).where(Document.id == document_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_active_by_email(self, email: str) -> Candidate | None:
        stmt = select(Candidate).where(
            func.lower(Candidate.email) == email.strip().lower(),
            Candidate.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_active_by_email_excluding_id(self, email: str, exclude_id: int) -> Candidate | None:
        stmt = select(Candidate).where(
            func.lower(Candidate.email) == email.strip().lower(),
            Candidate.deleted_at.is_(None),
            Candidate.id != exclude_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_active_by_phone_digits(self, phone_digits: str) -> Candidate | None:
        stmt = select(Candidate).where(
            _candidate_phone_digits_expr() == phone_digits,
            Candidate.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_active_by_phone_digits_excluding_id(
        self,
        phone_digits: str,
        exclude_id: int,
    ) -> Candidate | None:
        stmt = select(Candidate).where(
            _candidate_phone_digits_expr() == phone_digits,
            Candidate.deleted_at.is_(None),
            Candidate.id != exclude_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def _list_conditions(
        self,
        apply_status: str | None,
        search: str | None,
        target_job: str | None = None,
    ) -> list:
        conditions = [Candidate.deleted_at.is_(None)]
        if apply_status:
            conditions.append(Candidate.apply_status == apply_status)
        if search and search.strip():
            term = f"%{search.strip()}%"
            conditions.append(
                or_(
                    Candidate.name.ilike(term),
                    Candidate.email.ilike(term),
                )
            )
        if target_job and target_job.strip():
            conditions.append(Candidate.job_position == target_job.strip())
        return conditions

    async def count_list(
        self,
        apply_status: str | None = None,
        search: str | None = None,
        target_job: str | None = None,
    ) -> int:
        conditions = self._list_conditions(apply_status, search, target_job)
        stmt = select(func.count(Candidate.id)).where(*conditions)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def find_list(
        self,
        page: int,
        limit: int,
        apply_status: str | None = None,
        search: str | None = None,
        target_job: str | None = None,
    ) -> list[Candidate]:
        conditions = self._list_conditions(apply_status, search, target_job)
        offset = (page - 1) * limit
        stmt = (
            select(Candidate, Manager.name.label("created_name"))
            .outerjoin(Manager, Candidate.created_by == Manager.id)
            .where(*conditions)
            .order_by(Candidate.id.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        candidates: list[Candidate] = []
        for candidate, created_name in result.all():
            setattr(candidate, "created_name", created_name)
            candidates.append(candidate)
        return candidates

    async def count_active_candidates(self) -> int:
        stmt = select(func.count(Candidate.id)).where(Candidate.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def count_by_apply_status(self) -> list[tuple[str, int]]:
        stmt = (
            select(Candidate.apply_status, func.count(Candidate.id))
            .where(Candidate.deleted_at.is_(None))
            .group_by(Candidate.apply_status)
        )
        result = await self.db.execute(stmt)
        return [(str(row[0]), int(row[1])) for row in result.all()]

    async def count_by_target_job_distinct_candidates(self) -> list[tuple[str, int]]:
        stmt = (
            select(
                Candidate.job_position,
                func.count(Candidate.id),
            )
            .where(
                Candidate.deleted_at.is_(None),
                Candidate.job_position.is_not(None),
            )
            .group_by(Candidate.job_position)
        )
        result = await self.db.execute(stmt)
        return [(str(row[0]), int(row[1])) for row in result.all()]

    async def count_distinct_active_candidates_with_session(self) -> int:
        stmt = (
            select(func.count(distinct(InterviewSession.candidate_id)))
            .select_from(InterviewSession)
            .join(Candidate, Candidate.id == InterviewSession.candidate_id)
            .where(
                Candidate.deleted_at.is_(None),
                InterviewSession.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return int(result.scalar_one())
