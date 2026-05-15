"""프롬프트 프로필 관리 API 라우터다."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_active_manager
from models.manager import Manager
from schemas.prompt_profile import (
    PromptProfileCreateRequest,
    PromptProfileDeleteResponse,
    PromptProfileListResponse,
    PromptProfileResponse,
    PromptProfileUpdateRequest,
)
from services.prompt_profile_service import PromptProfileService

router = APIRouter(prefix="/prompt-profiles", tags=["프롬프트 프로필 관리"])


@router.get("",
            response_model=PromptProfileListResponse,
            summary="프롬프트 프로필 목록 조회")
async def list_prompt_profiles(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    target_job: str | None = Query(None, max_length=50),
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> PromptProfileListResponse:
    return await PromptProfileService.list_profiles(
        db=db,
        page=page,
        limit=limit,
        search=search,
        target_job=target_job,
    )


@router.get("/{profile_id}",
            response_model=PromptProfileResponse,
            summary="프롬프트 프로필 상세 조회")
async def get_prompt_profile(
    profile_id: int,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> PromptProfileResponse:
    return await PromptProfileService.get_profile(db=db, profile_id=profile_id)


@router.post("",
             response_model=PromptProfileResponse,
             status_code=status.HTTP_201_CREATED,
             summary="프롬프트 프로필 생성")
async def create_prompt_profile(
    request_body: PromptProfileCreateRequest,
    current_manager: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> PromptProfileResponse:
    return await PromptProfileService.create_profile(
        db=db,
        request=request_body,
        actor_id=current_manager.id,
    )


@router.put("/{profile_id}",
            response_model=PromptProfileResponse,
            summary="프롬프트 프로필 수정")
async def update_prompt_profile(
    profile_id: int,
    request_body: PromptProfileUpdateRequest,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> PromptProfileResponse:
    return await PromptProfileService.update_profile(
        db=db,
        profile_id=profile_id,
        request=request_body,
    )


@router.delete("/{profile_id}",
               response_model=PromptProfileDeleteResponse,
               summary="프롬프트 프로필 논리 삭제")
async def delete_prompt_profile(
    profile_id: int,
    current_manager: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> PromptProfileDeleteResponse:
    return await PromptProfileService.delete_profile(
        db=db,
        profile_id=profile_id,
        actor_id=current_manager.id,
    )

