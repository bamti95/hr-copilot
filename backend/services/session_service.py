import math
from datetime import datetime, timezone

from fastapi import BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ai.interview_graph.schemas import InterviewQuestionItem, ReviewResult
from core.config import settings
from core.database import get_db
from repositories.candidate_repository import CandidateRepository
from repositories.interview_question_repository import InterviewQuestionRepository
from repositories.prompt_profile_repository import PromptProfileRepository
from repositories.session_repo import SessionRepository
from schemas.session import (
    SessionCreateRequest,
    SessionDeleteResponse,
    SessionDetailResponse,
    SessionGenerateQuestionsRequest,
    SessionQuestionGenerationData,
    SessionListData,
    SessionPagination,
    SessionResponse,
    SessionTriggerData,
    SessionUpdateRequest,
)
from services.question_generation_service import (
    QuestionGenerationService,
    run_question_generation_background_job,
)
from services.session_generation_payload_assembler import SessionGenerationPayloadAssembler


class SessionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.session_repo = SessionRepository(db)
        self.candidate_repo = CandidateRepository(db)
        self.prompt_profile_repo = PromptProfileRepository(db)
        self.question_repo = InterviewQuestionRepository(db)
        self.question_generation_service = QuestionGenerationService(db)

    async def create_session(
        self,
        request: SessionCreateRequest,
        actor_id: int | None,
        background_tasks: BackgroundTasks,
        *,
        graph_impl: str = "default",
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
        await self.session_repo.mark_question_generation_queued(entity)
        await self.session_repo.flush()
        await self.db.commit()
        background_tasks.add_task(
            run_question_generation_background_job,
            entity.id,
            actor_id,
            None,
            graph_impl,
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
        background_tasks: BackgroundTasks,
    ) -> SessionTriggerData:
        entity = await self.session_repo.find_by_id_not_deleted(session_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="면접 세션을 찾을 수 없습니다.",
            )

        await self.session_repo.mark_question_generation_queued(entity)
        await self.db.commit()
        background_tasks.add_task(
            run_question_generation_background_job,
            entity.id,
            actor_id,
            request.target_question_ids,
        )

        return SessionTriggerData(
            session_id=entity.id,
            trigger_type=request.trigger_type.strip(),
            question_generation_status=entity.question_generation_status,
        )

    async def get_question_generation_status(
        self,
        session_id: int,
    ) -> SessionQuestionGenerationData:
        entity = await self.session_repo.find_by_id_not_deleted(session_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="면접 세션을 찾을 수 없습니다.",
            )

        questions = await self.question_repo.find_active_by_session_id(session_id)

        # Reconcile inconsistent state:
        # - Sometimes questions are already stored, but session status/progress remains QUEUED/PROCESSING.
        if entity.question_generation_status in {"QUEUED", "PROCESSING"} and questions:
            inferred_status = self._infer_question_generation_final_status(questions)
            await self.session_repo.mark_question_generation_completed(
                entity,
                status=inferred_status,
                error=entity.question_generation_error,
                refresh_completed_timestamp=entity.question_generation_completed_at is None,
            )
            await self.db.commit()

        # Even when status is already terminal, progress can be left in PROCESSING due to partial DB updates.
        if entity.question_generation_status in {"COMPLETED", "PARTIAL_COMPLETED"}:
            progress = entity.question_generation_progress or []
            if any(step.get("status") == "PROCESSING" for step in progress):
                await self.session_repo.mark_question_generation_completed(
                    entity,
                    status=entity.question_generation_status,
                    error=entity.question_generation_error,
                    refresh_completed_timestamp=False,
                )
                await self.db.commit()

        # Stale protection should not override a successful run that already produced questions.
        if not questions and self._is_stale_question_generation(entity):
            await self.session_repo.mark_question_generation_completed(
                entity,
                status="FAILED",
                error=(
                    "질문 생성 작업이 제한 시간 안에 완료되지 않아 실패로 처리했습니다. "
                    "전체 재생성으로 다시 요청해 주세요."
                ),
            )
            await self.db.commit()
        return SessionQuestionGenerationData(
            session_id=entity.id,
            status=entity.question_generation_status,
            error=entity.question_generation_error,
            requested_at=entity.question_generation_requested_at,
            completed_at=entity.question_generation_completed_at,
            progress=entity.question_generation_progress or [],
            generation_source={
                "entrypoint": "services.question_generation_service.run_question_generation_background_job",
                "service": "QuestionGenerationService.generate_and_store_for_session",
                "graph_runner": "ai.interview_graph.runner.run_interview_question_graph",
                "graph": "BuildState -> Analyzer -> Questioner -> Predictor -> Driller -> Reviewer -> Scorer -> Router -> Selector -> FinalFormatter",
            },
            questions=[
                InterviewQuestionItem(
                    id=str(question.id),
                    category=question.category,
                    question_text=question.question_text,
                    generation_basis=question.question_rationale or "",
                    document_evidence=question.document_evidence or [],
                    evaluation_guide=question.evaluation_guide or "",
                    predicted_answer=question.expected_answer or "",
                    predicted_answer_basis=question.expected_answer_basis or "",
                    follow_up_question=question.follow_up_question or "",
                    follow_up_basis=question.follow_up_basis or "",
                    risk_tags=question.risk_tags or [],
                    competency_tags=question.competency_tags or [],
                    review=ReviewResult(
                        question_id=str(question.id),
                        status=question.review_status
                        if question.review_status
                        in {"approved", "needs_revision", "rejected"}
                        else "rejected",
                        reason=question.review_reason or "",
                        reject_reason=question.review_reject_reason or "",
                        recommended_revision=question.review_recommended_revision or "",
                    ),
                    score=question.score or 0,
                    score_reason=question.score_reason or "",
                )
                for question in questions
            ],
        )

    @staticmethod
    def _infer_question_generation_final_status(questions) -> str:
        """
        Best-effort inference when DB state is inconsistent.
        - COMPLETED: enough questions exist and most core fields are present.
        - PARTIAL_COMPLETED: questions exist but look incomplete.
        """
        if not questions:
            return "FAILED"

        # Typical pipeline selects 5 questions; treat <5 as partial.
        if len(questions) < 5:
            return "PARTIAL_COMPLETED"

        def _is_present(value) -> bool:
            if value is None:
                return False
            if isinstance(value, str):
                return bool(value.strip())
            return True

        completed_like = 0
        for q in questions[:5]:
            core_fields = [
                q.question_text,
                q.expected_answer,
                q.follow_up_question,
                q.review_status,
                q.score,
            ]
            if sum(1 for v in core_fields if _is_present(v)) >= 4:
                completed_like += 1

        return "COMPLETED" if completed_like >= 4 else "PARTIAL_COMPLETED"

    @staticmethod
    def _is_stale_question_generation(entity) -> bool:
        if entity.question_generation_status not in {"QUEUED", "PROCESSING"}:
            return False

        started_at = entity.question_generation_requested_at or entity.created_at
        if started_at is None:
            return False
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)

        elapsed = datetime.now(timezone.utc) - started_at
        return elapsed.total_seconds() > settings.QUESTION_GENERATION_STALE_SECONDS


def get_session_service(db: AsyncSession = Depends(get_db)) -> SessionService:
    return SessionService(db)
