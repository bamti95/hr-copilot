import json
import logging

from fastapi import APIRouter, Depends, Query, status

from dependencies.auth import get_current_active_manager
from models.manager import Manager
from schemas.session import (
    SessionCreateRequest,
    SessionDeleteResultResponse,
    SessionDetailSingleResponse,
    SessionGenerateQuestionsRequest,
    SessionListResponse,
    SessionQuestionGenerationResponse,
    SessionSingleResponse,
    SessionTriggerResponse,
    SessionUpdateRequest,
)
from services.session_service import SessionService, get_session_service

router = APIRouter(prefix="/interview-sessions", tags=["interview-sessions"])
logger = logging.getLogger(__name__)


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


@router.get(
    "/{session_id}/question-generation",
    response_model=SessionQuestionGenerationResponse,
)
async def get_question_generation_status(
    session_id: int,
    _: Manager = Depends(get_current_active_manager),
    service: SessionService = Depends(get_session_service),
) -> SessionQuestionGenerationResponse:
    data = await service.get_question_generation_status(session_id=session_id)
    return SessionQuestionGenerationResponse(
        data=data,
        message="질문 생성 상태 조회 성공",
    )


@router.get("/{session_id}", response_model=SessionDetailSingleResponse)
async def get_session(
    session_id: int,
    _: Manager = Depends(get_current_active_manager),
    service: SessionService = Depends(get_session_service),
) -> SessionDetailSingleResponse:
    data = await service.get_session(session_id=session_id)
    return SessionDetailSingleResponse(
        data=data,
        message="면접 세션 조회 성공",
    )


@router.post("", response_model=SessionSingleResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request_body: SessionCreateRequest,
    current_manager: Manager = Depends(get_current_active_manager),
    service: SessionService = Depends(get_session_service),
) -> SessionSingleResponse:
    logger.info(
        "Session Create Request Payload\n%s",
        json.dumps(
            {
                "actor_id": current_manager.id,
                "payload": request_body.model_dump(),
            },
            ensure_ascii=False,
            indent=2,
        ),
    )

    data = await service.create_session(
        request=request_body,
        actor_id=current_manager.id,
    )

    logger.info(
        "Session Create Success Response\n%s",
        json.dumps(
            {
                "actor_id": current_manager.id,
                "response": data.model_dump(mode="json"),
            },
            ensure_ascii=False,
            indent=2,
        ),
    )

    return SessionSingleResponse(
        data=data,
        message="면접 세션 생성 성공. 질문 생성 작업이 대기열에 등록되었습니다.",
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


@router.post("/{session_id}/generate-questions", response_model=SessionTriggerResponse)
async def generate_questions(
    session_id: int,
    request_body: SessionGenerateQuestionsRequest,
    current_manager: Manager = Depends(get_current_active_manager),
    service: SessionService = Depends(get_session_service),
) -> SessionTriggerResponse:
    data = await service.trigger_question_generation(
        session_id=session_id,
        request=request_body,
        actor_id=current_manager.id,
    )
    return SessionTriggerResponse(
        data=data,
        message="질문 생성 작업이 대기열에 등록되었습니다.",
    )
