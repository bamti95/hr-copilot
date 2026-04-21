from fastapi import APIRouter, Depends, Query, status

from dependencies.auth import get_current_active_manager
from models.manager import Manager
from schemas.session import (
    SessionCreateRequest,
    SessionDeleteResultResponse,
    SessionListResponse,
    SessionSingleResponse,
    SessionUpdateRequest,
)
from services.session_service import SessionService, get_session_service

router = APIRouter(prefix="/interview-sessions", tags=["interview-sessions"])


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    candidate_id: int | None = Query(None, gt=0),
    target_job: str | None = Query(None),
    _: Manager = Depends(get_current_active_manager),
    service: SessionService = Depends(get_session_service),
) -> SessionListResponse:
    data = await service.list_sessions(
        page=page,
        limit=limit,
        candidate_id=candidate_id,
        target_job=target_job,
    )
    return SessionListResponse(
        data=data,
        message="면접 세션 목록 조회 성공",
    )


@router.get("/{session_id}", response_model=SessionSingleResponse)
async def get_session(
    session_id: int,
    _: Manager = Depends(get_current_active_manager), 
    service: SessionService = Depends(get_session_service),
) -> SessionSingleResponse:
    data = await service.get_session(session_id=session_id)
    return SessionSingleResponse(
        data=data,
        message="면접 세션 조회 성공",
    )


@router.post("", response_model=SessionSingleResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request_body: SessionCreateRequest,
    current_manager: Manager = Depends(get_current_active_manager),
    service: SessionService = Depends(get_session_service),
) -> SessionSingleResponse:
    data = await service.create_session(
        request=request_body,
        actor_id=current_manager.id,
    )
    return SessionSingleResponse(
        data=data,
        message="면접 세션 생성 성공",
    )


@router.put("/{session_id}", response_model=SessionSingleResponse)
async def update_session(
    session_id: int,
    request_body: SessionUpdateRequest,
    _: Manager = Depends(get_current_active_manager),
    service: SessionService = Depends(get_session_service),
) -> SessionSingleResponse:
    data = await service.update_session(
        session_id=session_id,
        request=request_body,
    )
    return SessionSingleResponse(
        data=data,
        message="면접 세션 수정 성공",
    )


@router.delete("/{session_id}", response_model=SessionDeleteResultResponse)
async def delete_session(
    session_id: int,
    current_manager: Manager = Depends(get_current_active_manager),
    service: SessionService = Depends(get_session_service),
) -> SessionDeleteResultResponse:
    data = await service.delete_session(
        session_id=session_id,
        actor_id=current_manager.id,
    )
    return SessionDeleteResultResponse(
        data=data,
        message="면접 세션 삭제 성공",
    )
