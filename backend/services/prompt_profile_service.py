import json
import math
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.prompt_profile import PromptProfile
from repositories.prompt_profile_repository import PromptProfileRepository
from schemas.prompt_profile import (
    PromptProfileCreateRequest,
    PromptProfileDeleteResponse,
    PromptProfileListResponse,
    PromptProfilePagination,
    PromptProfileResponse,
    PromptProfileUpdateRequest,
)

_UNCHANGED = object()


def _http_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
    )


def _normalize_output_schema_for_create(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    try:
        json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise _http_error(
            status.HTTP_400_BAD_REQUEST,
            "INVALID_JSON_SCHEMA",
            "유효하지 않은 JSON 스키마입니다.",
        ) from exc
    return stripped


def _normalize_output_schema_for_update(
    request: PromptProfileUpdateRequest,
) -> str | None | object:
    """Return _UNCHANGED if field omitted; otherwise str | None for DB."""
    if "output_schema" not in request.model_fields_set:
        return _UNCHANGED
    raw = request.output_schema
    if raw is None:
        return None
    stripped = raw.strip()
    if not stripped:
        return None
    try:
        json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise _http_error(
            status.HTTP_400_BAD_REQUEST,
            "INVALID_JSON_SCHEMA",
            "유효하지 않은 JSON 스키마입니다.",
        ) from exc
    return stripped


class PromptProfileService:
    @staticmethod
    async def create_profile(
        db: AsyncSession,
        request: PromptProfileCreateRequest,
        actor_id: int | None,
    ) -> PromptProfileResponse:
        output_schema = _normalize_output_schema_for_create(request.output_schema)
        now = datetime.now(timezone.utc)
        repo = PromptProfileRepository(db)

        if await repo.find_active_by_profile_key(request.profile_key):
            raise _http_error(
                status.HTTP_400_BAD_REQUEST,
                "DUPLICATE_PROFILE_KEY",
                "이미 존재하는 프로파일 키입니다.",
            )

        target_job = request.target_job.strip() if request.target_job and request.target_job.strip() else None
        entity = PromptProfile(
            profile_key=request.profile_key.strip(),
            system_prompt=request.system_prompt.strip(),
            output_schema=output_schema,
            target_job=target_job,
            created_by=actor_id,
            updated_at=now,
        )
        await repo.add(entity)
        try:
            await repo.flush()
            await db.commit()
        except IntegrityError as exc:
            await db.rollback()
            raise _http_error(
                status.HTTP_400_BAD_REQUEST,
                "DUPLICATE_PROFILE_KEY",
                "이미 존재하는 프로파일 키입니다.",
            ) from exc

        await repo.refresh(entity)
        return PromptProfileResponse.model_validate(entity)

    @staticmethod
    async def list_profiles(
        db: AsyncSession,
        page: int,
        limit: int,
        search: str | None,
        target_job: str | None,
    ) -> PromptProfileListResponse:
        repo = PromptProfileRepository(db)
        job_filter = target_job.strip() if target_job and target_job.strip() else None
        total_items = await repo.count_list(search=search, target_job=job_filter)
        rows = await repo.find_list(page=page, limit=limit, search=search, target_job=job_filter)
        total_pages = math.ceil(total_items / limit) if total_items else 0
        return PromptProfileListResponse(
            prompt_profiles=[PromptProfileResponse.model_validate(row) for row in rows],
            pagination=PromptProfilePagination(
                current_page=page,
                total_pages=total_pages,
                total_items=total_items,
                items_per_page=limit,
            ),
        )

    @staticmethod
    async def get_profile(db: AsyncSession, profile_id: int) -> PromptProfileResponse:
        repo = PromptProfileRepository(db)
        entity = await repo.find_by_id_active(profile_id)
        if not entity:
            raise _http_error(
                status.HTTP_404_NOT_FOUND,
                "PROFILE_NOT_FOUND",
                "프롬프트 프로파일을 찾을 수 없습니다.",
            )
        return PromptProfileResponse.model_validate(entity)

    @staticmethod
    async def update_profile(
        db: AsyncSession,
        profile_id: int,
        request: PromptProfileUpdateRequest,
    ) -> PromptProfileResponse:
        repo = PromptProfileRepository(db)
        entity = await repo.find_by_id_active(profile_id)
        if not entity:
            raise _http_error(
                status.HTTP_404_NOT_FOUND,
                "PROFILE_NOT_FOUND",
                "프롬프트 프로파일을 찾을 수 없습니다.",
            )

        schema_update = _normalize_output_schema_for_update(request)
        entity.system_prompt = request.system_prompt.strip()
        if schema_update is not _UNCHANGED:
            assert isinstance(schema_update, (str, type(None)))
            entity.output_schema = schema_update
        entity.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await repo.refresh(entity)
        return PromptProfileResponse.model_validate(entity)

    @staticmethod
    async def delete_profile(
        db: AsyncSession,
        profile_id: int,
        actor_id: int | None,
    ) -> PromptProfileDeleteResponse:
        repo = PromptProfileRepository(db)
        entity = await repo.find_by_id_any(profile_id)
        if not entity or entity.deleted_at is not None:
            if not entity:
                raise _http_error(
                    status.HTTP_404_NOT_FOUND,
                    "PROFILE_NOT_FOUND",
                    "프롬프트 프로파일을 찾을 수 없습니다.",
                )
            raise _http_error(
                status.HTTP_400_BAD_REQUEST,
                "ALREADY_DELETED",
                "이미 삭제된 프로필입니다.",
            )

        now = datetime.now(timezone.utc)
        entity.deleted_at = now
        entity.deleted_by = actor_id
        await db.commit()
        await repo.refresh(entity)
        return PromptProfileDeleteResponse(
            id=entity.id,
            deleted_at=entity.deleted_at,  # type: ignore[arg-type]
            deleted_by=entity.deleted_by,
        )
