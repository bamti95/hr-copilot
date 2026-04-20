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

router = APIRouter(prefix="/prompt-profiles", tags=["prompt-profile"])


@router.get("", response_model=PromptProfileListResponse)
async def list_prompt_profiles(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> PromptProfileListResponse:
    return await PromptProfileService.list_profiles(
        db=db,
        page=page,
        limit=limit,
        search=search,
    )


@router.get("/{profile_id}", response_model=PromptProfileResponse)
async def get_prompt_profile(
    profile_id: int,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> PromptProfileResponse:
    return await PromptProfileService.get_profile(db=db, profile_id=profile_id)


@router.post("", response_model=PromptProfileResponse, status_code=status.HTTP_201_CREATED)
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


@router.put("/{profile_id}", response_model=PromptProfileResponse)
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


@router.delete("/{profile_id}", response_model=PromptProfileDeleteResponse)
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
