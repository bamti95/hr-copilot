"""후보자 관련 조회 리포지토리.

후보자 본문 조회, 문서 조회, 중복 체크, 목록 검색, 대시보드 집계를 담당한다.
이메일과 전화번호 중복 판단 규칙, 직무명 필터 정규화 규칙이 이 파일의 핵심이다.
"""

from sqlalchemy import distinct, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.manager import Manager
from models.interview_session import InterviewSession
from models.candidate import Candidate
from models.document import Document
from common.job_position import JOB_POSITION_ALIASES, JOB_POSITION_LABELS, normalize_job_position_code
from repositories.base_repository import BaseRepository


def _candidate_phone_digits_expr():
    """전화번호를 숫자만 남긴 형태로 만든다.

    하이픈이나 공백 형식이 달라도 같은 번호로 비교하기 위한 식이다.
    """
    return func.regexp_replace(Candidate.phone, "[^0-9]", "", "g")


class CandidateRepository(BaseRepository[Candidate]):
    """후보자 엔터티 조회와 중복 검사를 담당한다."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Candidate)

    async def find_by_id_not_deleted(self, candidate_id: int) -> Candidate | None:
        """삭제되지 않은 후보자 1건을 생성자 이름과 함께 조회한다."""
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
        """삭제 여부와 관계없이 후보자 1건을 조회한다."""
        stmt = select(Candidate).where(Candidate.id == candidate_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_active_documents_by_candidate_id(self, candidate_id: int) -> list[Document]:
        """후보자에 연결된 활성 문서를 최신순으로 조회한다."""
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
        """후보자 범위 안에서 활성 문서 1건을 조회한다."""
        stmt = select(Document).where(
            Document.id == document_id,
            Document.candidate_id == candidate_id,
            Document.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_document_by_id_any(self, document_id: int) -> Document | None:
        """삭제 여부와 관계없이 문서 1건을 조회한다."""
        stmt = select(Document).where(Document.id == document_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_active_by_email(self, email: str) -> Candidate | None:
        """이메일 중복 체크용 활성 후보자 조회다.

        대소문자 차이는 무시한다.
        """
        stmt = select(Candidate).where(
            func.lower(Candidate.email) == email.strip().lower(),
            Candidate.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_active_by_email_excluding_id(self, email: str, exclude_id: int) -> Candidate | None:
        """자기 자신을 제외한 이메일 중복 후보자를 찾는다."""
        stmt = select(Candidate).where(
            func.lower(Candidate.email) == email.strip().lower(),
            Candidate.deleted_at.is_(None),
            Candidate.id != exclude_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_active_by_phone_digits(self, phone_digits: str) -> Candidate | None:
        """숫자만 남긴 전화번호로 활성 후보자를 찾는다."""
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
        """자기 자신을 제외한 전화번호 중복 후보자를 찾는다."""
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
        """후보자 목록 공통 검색 조건을 만든다.

        직무 필터는 별칭과 표시 이름까지 함께 허용해 운영 편의를 높인다.
        """
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
            normalized_job = normalize_job_position_code(target_job)
            if normalized_job:
                alias_terms = {
                    normalized_job,
                    JOB_POSITION_LABELS[normalized_job],
                    *JOB_POSITION_ALIASES[normalized_job],
                }
                conditions.append(
                    or_(
                        Candidate.job_position == normalized_job,
                        Candidate.job_position.ilike(f"{normalized_job} (%)"),
                        *[
                            Candidate.job_position.ilike(f"%{alias}%")
                            for alias in alias_terms
                            if alias
                        ],
                    )
                )
            else:
                conditions.append(Candidate.job_position == target_job.strip())
        return conditions

    async def count_list(
        self,
        apply_status: str | None = None,
        search: str | None = None,
        target_job: str | None = None,
    ) -> int:
        """후보자 목록 수를 계산한다."""
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
        """후보자 목록을 생성자 이름과 함께 페이지 단위로 조회한다."""
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
        """삭제되지 않은 후보자 총수를 반환한다."""
        stmt = select(func.count(Candidate.id)).where(Candidate.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def count_by_apply_status(self) -> list[tuple[str, int]]:
        """지원 상태별 후보자 수를 집계한다."""
        stmt = (
            select(Candidate.apply_status, func.count(Candidate.id))
            .where(Candidate.deleted_at.is_(None))
            .group_by(Candidate.apply_status)
        )
        result = await self.db.execute(stmt)
        return [(str(row[0]), int(row[1])) for row in result.all()]

    async def count_by_target_job_distinct_candidates(self) -> list[tuple[str, int]]:
        """직무별 후보자 수를 집계한다."""
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
        """면접 세션이 하나 이상 있는 활성 후보자 수를 센다."""
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
