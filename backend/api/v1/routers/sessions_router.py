import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status

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


async def _create_session_core(
    request_body: SessionCreateRequest,
    background_tasks: BackgroundTasks,
    current_manager: Manager,
    service: SessionService,
    *,
    graph_impl: str,
    success_message: str,
) -> SessionSingleResponse:
    logger.info(
        "Session Create Request Payload\n%s",
        json.dumps(
            {
                "actor_id": current_manager.id,
                "graph_impl": graph_impl,
                "payload": request_body.model_dump(),
            },
            ensure_ascii=False,
            indent=2,
        ),
    )

    data = await service.create_session(
        request=request_body,
        actor_id=current_manager.id,
        background_tasks=background_tasks,
        graph_impl=graph_impl,
    )

    logger.info(
        "Session Create Success Response\n%s",
        json.dumps(
            {
                "actor_id": current_manager.id,
                "graph_impl": graph_impl,
                "response": data.model_dump(mode="json"),
            },
            ensure_ascii=False,
            indent=2,
        ),
    )

    return SessionSingleResponse(
        data=data,
        message=success_message,
    )


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
    background_tasks: BackgroundTasks,
    current_manager: Manager = Depends(get_current_active_manager),
    service: SessionService = Depends(get_session_service),
) -> SessionSingleResponse:
    return await _create_session_core(
        request_body,
        background_tasks,
        current_manager,
        service,
        graph_impl="default",
        success_message="면접 세션 생성 성공. 질문 생성 작업이 대기열에 등록되었습니다.",
    )


@router.post("/pipeline/jh", response_model=SessionSingleResponse, status_code=status.HTTP_201_CREATED)
async def create_session_jh(
    request_body: SessionCreateRequest,
    background_tasks: BackgroundTasks,
    current_manager: Manager = Depends(get_current_active_manager),
    service: SessionService = Depends(get_session_service),
) -> SessionSingleResponse:
    return await _create_session_core(
        request_body,
        background_tasks,
        current_manager,
        service,
        graph_impl="jh",
        success_message="면접 세션 생성 성공. 질문 생성 작업이 대기열에 등록되었습니다. (그래프: jh)",
    )


@router.post("/pipeline/hy", response_model=SessionSingleResponse, status_code=status.HTTP_201_CREATED)
async def create_session_hy(
    request_body: SessionCreateRequest,
    background_tasks: BackgroundTasks,
    current_manager: Manager = Depends(get_current_active_manager),
    service: SessionService = Depends(get_session_service),
) -> SessionSingleResponse:
    return await _create_session_core(
        request_body,
        background_tasks,
        current_manager,
        service,
        graph_impl="hy",
        success_message="면접 세션 생성 성공. 질문 생성 작업이 대기열에 등록되었습니다. (그래프: hy)",
    )


@router.post("/pipeline/jy", response_model=SessionSingleResponse, status_code=status.HTTP_201_CREATED)
async def create_session_jy(
    request_body: SessionCreateRequest,
    background_tasks: BackgroundTasks,
    current_manager: Manager = Depends(get_current_active_manager),
    service: SessionService = Depends(get_session_service),
) -> SessionSingleResponse:
    return await _create_session_core(
        request_body,
        background_tasks,
        current_manager,
        service,
        graph_impl="jy",
        success_message="면접 세션 생성 성공. 질문 생성 작업이 대기열에 등록되었습니다. (그래프: jy)",
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
    background_tasks: BackgroundTasks,
    current_manager: Manager = Depends(get_current_active_manager),
    service: SessionService = Depends(get_session_service),
) -> SessionTriggerResponse:
    data = await service.trigger_question_generation(
        session_id=session_id,
        request=request_body,
        actor_id=current_manager.id,
        background_tasks=background_tasks,
    )
    return SessionTriggerResponse(
        data=data,
        message="질문 생성 작업이 대기열에 등록되었습니다.",
    )
