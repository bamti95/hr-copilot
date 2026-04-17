import math
import re
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.candidate import ApplyStatus, Candidate
from repositories.candidate_repository import CandidateRepository
from schemas.candidate import (
    CandidateCreateRequest,
    CandidateDeleteResponse,
    CandidateListResponse,
    CandidatePagination,
    CandidateResponse,
    CandidateStatusPatchRequest,
    CandidateStatusPatchResponse,
    CandidateUpdateRequest,
)


def _assert_extra_email_rules(email: str) -> None:
    normalized = email.strip()
    if "@" not in normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 이메일 형식입니다.",
        )
    local, _, domain = normalized.partition("@")
    if not local or not domain or "." not in domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 이메일 형식입니다.",
        )


def _assert_phone_format(phone: str) -> None:
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 10 or len(digits) > 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 전화번호 형식입니다.",
        )


class CandidateService:
    @staticmethod
    async def create_candidate(
        db: AsyncSession,
        request: CandidateCreateRequest,
        actor_id: int | None,
    ) -> CandidateResponse:
        _assert_extra_email_rules(str(request.email))
        _assert_phone_format(request.phone)

        repo = CandidateRepository(db)
        if await repo.find_active_by_email(str(request.email)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 이메일입니다.",
            )

        entity = Candidate(
            name=request.name.strip(),
            email=str(request.email).strip(),
            phone=request.phone.strip(),
            birth_date=request.birth_date,
            apply_status=ApplyStatus.APPLIED.value,
            created_by=actor_id,
        )
        await repo.add(entity)
        await repo.flush()
        await db.commit()
        await repo.refresh(entity)
        return CandidateResponse.model_validate(entity)

    @staticmethod
    async def list_candidates(
        db: AsyncSession,
        page: int,
        limit: int,
        apply_status: ApplyStatus | None,
        search: str | None,
    ) -> CandidateListResponse:
        repo = CandidateRepository(db)
        status_str = apply_status.value if apply_status else None
        total_items = await repo.count_list(apply_status=status_str, search=search)
        rows = await repo.find_list(
            page=page,
            limit=limit,
            apply_status=status_str,
            search=search,
        )
        total_pages = math.ceil(total_items / limit) if total_items else 0
        return CandidateListResponse(
            candidates=[CandidateResponse.model_validate(r) for r in rows],
            pagination=CandidatePagination(
                current_page=page,
                total_pages=total_pages,
                total_items=total_items,
                items_per_page=limit,
            ),
        )

    @staticmethod
    async def get_candidate(db: AsyncSession, candidate_id: int) -> CandidateResponse:
        repo = CandidateRepository(db)
        entity = await repo.find_by_id_not_deleted(candidate_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="지원자를 찾을 수 없습니다.",
            )
        return CandidateResponse.model_validate(entity)

    @staticmethod
    async def update_candidate(
        db: AsyncSession,
        candidate_id: int,
        request: CandidateUpdateRequest,
    ) -> CandidateResponse:
        _assert_extra_email_rules(str(request.email))
        _assert_phone_format(request.phone)

        repo = CandidateRepository(db)
        entity = await repo.find_by_id_not_deleted(candidate_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="지원자를 찾을 수 없습니다.",
            )

        if await repo.find_active_by_email_excluding_id(str(request.email), candidate_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 이메일입니다.",
            )

        entity.name = request.name.strip()
        entity.email = str(request.email).strip()
        entity.phone = request.phone.strip()
        entity.birth_date = request.birth_date
        entity.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await repo.refresh(entity)
        return CandidateResponse.model_validate(entity)

    @staticmethod
    async def patch_status(
        db: AsyncSession,
        candidate_id: int,
        request: CandidateStatusPatchRequest,
    ) -> CandidateStatusPatchResponse:
        repo = CandidateRepository(db)
        entity = await repo.find_by_id_not_deleted(candidate_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="지원자를 찾을 수 없습니다.",
            )

        try:
            next_status = ApplyStatus(request.apply_status.strip())
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="유효하지 않은 상태값입니다.",
            ) from exc

        entity.apply_status = next_status.value
        entity.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await repo.refresh(entity)
        return CandidateStatusPatchResponse(id=entity.id, apply_status=entity.apply_status)

    @staticmethod
    async def delete_candidate(
        db: AsyncSession,
        candidate_id: int,
        actor_id: int | None,
    ) -> CandidateDeleteResponse:
        repo = CandidateRepository(db)
        entity = await repo.find_by_id_any(candidate_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="지원자를 찾을 수 없습니다.",
            )
        if entity.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 삭제된 지원자입니다.",
            )

        now = datetime.now(timezone.utc)
        entity.deleted_at = now
        entity.deleted_by = actor_id
        entity.updated_at = now

        await db.commit()
        await repo.refresh(entity)
        return CandidateDeleteResponse(
            id=entity.id,
            deleted_at=entity.deleted_at,
            deleted_by=entity.deleted_by,
        )
