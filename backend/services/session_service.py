import math
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from repositories.candidate_repository import CandidateRepository
from repositories.prompt_profile_repository import PromptProfileRepository
from repositories.session_repo import SessionRepository
from schemas.session import (
    SessionCreateRequest,
    SessionDeleteResponse,
    SessionDetailResponse,
    SessionGenerateQuestionsRequest,
    SessionListData,
    SessionPagination,
    SessionResponse,
    SessionTriggerData,
    SessionUpdateRequest,
)
from services.question_generation_service import QuestionGenerationService
from services.session_generation_payload_assembler import SessionGenerationPayloadAssembler


class SessionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.session_repo = SessionRepository(db)
        self.candidate_repo = CandidateRepository(db)
        self.prompt_profile_repo = PromptProfileRepository(db)
        self.question_generation_service = QuestionGenerationService()

    async def create_session(
        self,
        request: SessionCreateRequest,
        actor_id: int | None,
    ) -> SessionResponse:
        candidate = await self.candidate_repo.find_by_id_not_deleted(request.candidate_id)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="지원자를 찾을 수 없습니다.",
            )

        prompt_profile = await self.prompt_profile_repo.find_by_id_active(
            request.prompt_profile_id
        )
        if not prompt_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="프롬프트 프로필을 찾을 수 없습니다.",
            )

        entity = await self.session_repo.add(
            self.session_repo.model(
                candidate_id=request.candidate_id,
                target_job=request.target_job.strip(),
                difficulty_level=request.difficulty_level.strip() if request.difficulty_level else None,
                prompt_profile_id=request.prompt_profile_id,
                created_by=actor_id,
            )
        )
        await self.session_repo.flush()
        await self.db.commit()

        assembler = SessionGenerationPayloadAssembler(self.db)
        generation_payload = await assembler.build_candidate_interview_prep_input(entity.id)
        await self.question_generation_service.request_candidate_interview_prep(
            generation_payload
        )

        detail = await self.session_repo.get_detail_with_candidate(entity.id)
        if not detail:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="면접 세션 생성 결과를 불러오지 못했습니다.",
            )
        return SessionResponse.model_validate(detail)

    async def list_sessions(
        self,
        page: int,
        limit: int,
        candidate_id: int | None,
        target_job: str | None,
    ) -> SessionListData:
        total_items = await self.session_repo.count_list(
            candidate_id=candidate_id,
            target_job=target_job,
        )
        rows = await self.session_repo.find_list(
            page=page,
            limit=limit,
            candidate_id=candidate_id,
            target_job=target_job,
        )
        total_pages = math.ceil(total_items / limit) if total_items else 0

        return SessionListData(
            interview_sessions=[SessionResponse.model_validate(row) for row in rows],
            pagination=SessionPagination(
                current_page=page,
                total_pages=total_pages,
                total_items=total_items,
                items_per_page=limit,
            ),
        )

    async def get_session(self, session_id: int) -> SessionDetailResponse:
        entity = await self.session_repo.get_detail_with_candidate(session_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="면접 세션을 찾을 수 없습니다.",
            )
        assembler = SessionGenerationPayloadAssembler(self.db)
        assembled_payload_preview = await assembler.build_candidate_interview_prep_input(
            session_id
        )
        data = SessionResponse.model_validate(entity)
        return SessionDetailResponse(
            **data.model_dump(mode="python"),
            assembled_payload_preview=assembled_payload_preview,
        )

    async def update_session(
        self,
        session_id: int,
        request: SessionUpdateRequest,
    ) -> SessionResponse:
        entity = await self.session_repo.find_by_id_not_deleted(session_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="면접 세션을 찾을 수 없습니다.",
            )

        entity.target_job = request.target_job.strip()
        entity.difficulty_level = request.difficulty_level.strip() if request.difficulty_level else None

        await self.db.commit()

        detail = await self.session_repo.get_detail_with_candidate(session_id)
        if not detail:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="면접 세션 수정 결과를 불러오지 못했습니다.",
            )
        return SessionResponse.model_validate(detail)

    async def delete_session(
        self,
        session_id: int,
        actor_id: int | None,
    ) -> SessionDeleteResponse:
        entity = await self.session_repo.find_by_id_any(session_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="면접 세션을 찾을 수 없습니다.",
            )
        if entity.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 삭제된 면접 세션입니다.",
            )

        now = datetime.now(timezone.utc)
        entity.deleted_at = now
        entity.deleted_by = actor_id

        await self.db.commit()
        await self.session_repo.refresh(entity)
        return SessionDeleteResponse.model_validate(entity)

    async def trigger_question_generation(
        self,
        session_id: int,
        request: SessionGenerateQuestionsRequest,
        actor_id: int | None,
    ) -> SessionTriggerData:
        entity = await self.session_repo.find_by_id_not_deleted(session_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="면접 세션을 찾을 수 없습니다.",
            )

        # Placeholder trigger only. A later step can replace this with
        # actual queueing / LangGraph orchestration while keeping the API stable.
        _ = actor_id

        return SessionTriggerData(
            session_id=entity.id,
            trigger_type=request.trigger_type.strip(),
        )


def get_session_service(db: AsyncSession = Depends(get_db)) -> SessionService:
    return SessionService(db)
