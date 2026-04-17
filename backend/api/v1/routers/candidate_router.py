from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_active_manager
from models.candidate import ApplyStatus
from models.manager import Manager
from schemas.candidate import (
    CandidateCreateRequest,
    CandidateDeleteResponse,
    CandidateListResponse,
    CandidateResponse,
    CandidateStatisticsResponse,
    CandidateStatusPatchRequest,
    CandidateStatusPatchResponse,
    CandidateUpdateRequest,
)
from services.candidate_service import CandidateService

router = APIRouter(prefix="/candidates", tags=["candidate"])


@router.get("", response_model=CandidateListResponse)
async def list_candidates(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    apply_status: ApplyStatus | None = Query(None),
    search: str | None = Query(None),
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> CandidateListResponse:
    return await CandidateService.list_candidates(
        db=db,
        page=page,
        limit=limit,
        apply_status=apply_status,
        search=search,
    )


@router.get("/statistics", response_model=CandidateStatisticsResponse)
async def get_candidate_statistics(
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> CandidateStatisticsResponse:
    return await CandidateService.get_statistics(db=db)


@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: int,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> CandidateResponse:
    return await CandidateService.get_candidate(db=db, candidate_id=candidate_id)


@router.post("", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def create_candidate(
    request_body: CandidateCreateRequest,
    current_manager: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> CandidateResponse:
    return await CandidateService.create_candidate(
        db=db,
        request=request_body,
        actor_id=current_manager.id,
    )


@router.put("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(
    candidate_id: int,
    request_body: CandidateUpdateRequest,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> CandidateResponse:
    return await CandidateService.update_candidate(
        db=db,
        candidate_id=candidate_id,
        request=request_body,
    )


@router.patch("/{candidate_id}/status", response_model=CandidateStatusPatchResponse)
async def patch_candidate_status(
    candidate_id: int,
    request_body: CandidateStatusPatchRequest,
    _: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> CandidateStatusPatchResponse:
    return await CandidateService.patch_status(
        db=db,
        candidate_id=candidate_id,
        request=request_body,
    )


@router.delete("/{candidate_id}", response_model=CandidateDeleteResponse)
async def delete_candidate(
    candidate_id: int,
    current_manager: Manager = Depends(get_current_active_manager),
    db: AsyncSession = Depends(get_db),
) -> CandidateDeleteResponse:
    return await CandidateService.delete_candidate(
        db=db,
        candidate_id=candidate_id,
        actor_id=current_manager.id,
    )
