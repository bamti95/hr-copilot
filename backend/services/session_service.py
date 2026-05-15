"""면접 세션 생명주기를 관리한다.

세션 생성과 수정, 질문 생성 트리거, 진행 상태 조회를 맡는다.
질문 생성은 시간이 걸릴 수 있으므로 동기 처리 대신
백그라운드 작업으로 넘기고 상태 필드로 진행 상황을 관리한다.
"""

import math
from datetime import datetime, timezone

from fastapi import BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ai.interview_graph.schemas import (
    InterviewQuestionItem,
    ReviewResult,
    normalize_question_category,
)
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
    """면접 세션 CRUD와 질문 생성 흐름을 관리하는 서비스다."""

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
        """면접 세션을 생성하고 질문 생성 작업을 큐에 올린다.

        세션을 만들자마자 질문 생성을 QUEUED 상태로 전환한다.
        실제 생성은 백그라운드에서 처리해 API 응답을 빠르게 돌려준다.
        """
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
        """면접 세션 목록과 페이지 정보를 반환한다."""
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
        """세션 상세와 질문 생성 입력 미리보기를 함께 반환한다."""
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
        """면접 세션의 기본 정보만 수정한다."""
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
        """면접 세션을 소프트 삭제한다."""
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
        """질문 생성을 다시 요청한다.

        전체 재생성뿐 아니라 일부 질문 재생성도 같은 진입점에서 처리한다.
        실제 생성 로직은 백그라운드 작업으로 넘긴다.
        """
        entity = await self.session_repo.find_by_id_not_deleted(session_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="면접 세션을 찾을 수 없습니다.",
            )

        await self.session_repo.mark_question_generation_queued(
            entity,
            request.graph_impl,
        )
        await self.db.commit()
        background_tasks.add_task(
            run_question_generation_background_job,
            entity.id,
            actor_id,
            request.target_question_ids,
            request.graph_impl,
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
        """질문 생성 상태와 현재 질문 목록을 함께 반환한다.

        저장 상태와 실제 질문 데이터가 어긋나는 경우가 있어
        이 함수에서 한 번 더 상태를 보정한다.
        대표적으로 질문은 이미 저장됐는데 세션 상태가
        QUEUED나 PROCESSING에 머무는 경우를 여기서 정리한다.
        """
        entity = await self.session_repo.find_by_id_not_deleted(session_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="면접 세션을 찾을 수 없습니다.",
            )

        questions = await self.question_repo.find_active_by_session_id(session_id)

        # Reconcile inconsistent state:
        # - Sometimes questions are already stored, but session status/progress remains QUEUED/PROCESSING.
        # - For selected regeneration, existing questions are present before the new job finishes,
        #   so question existence alone must not be treated as completion.
        if (
            entity.question_generation_status in {"QUEUED", "PROCESSING"}
            and questions
            and self._can_infer_generation_completed_from_progress(entity)
        ):
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
            generation_source=self._build_generation_source(
                entity.question_generation_progress or []
            ),
            questions=[
                InterviewQuestionItem(
                    id=str(question.id),
                    category=self._normalize_stored_question_category(question.category),
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
    def _normalize_stored_question_category(category: str | None) -> str:
        normalized = normalize_question_category(category)
        allowed_categories = {
            "기술 역량",
            "직무 역량",
            "경험 검증",
            "리스크 검증",
            "조직 적합성",
            "지원 동기",
            "커뮤니케이션",
            "기타",
        }
        if normalized in allowed_categories:
            return normalized

        raw = str(category or "").strip()
        upper = raw.upper()

        if any(token in raw for token in ("소통", "조정", "이해관계자", "협업", "갈등", "커뮤니케이션")):
            return "커뮤니케이션"
        if any(token in raw for token in ("조직", "문화", "적합", "피드백", "책임감")):
            return "조직 적합성"
        if any(token in raw for token in ("동기", "이유", "전환", "지원", "복귀")):
            return "지원 동기"
        if any(token in raw for token in ("리스크", "위험", "불확실", "공백", "검증")):
            return "리스크 검증"
        if any(token in raw for token in ("경험", "사례", "성과", "책임", "운영", "규모", "프로젝트")):
            return "경험 검증"
        if any(
            token in upper
            for token in ("API", "FASTAPI", "DOCKER", "AIRFLOW", "SPARK", "SQL", "ETL", "ML", "AI")
        ):
            return "기술 역량"

        return "기타"

    @staticmethod
    def _can_infer_generation_completed_from_progress(entity) -> bool:
        progress = entity.question_generation_progress or []
        if not progress:
            return True
        last_step = progress[-1]
        return last_step.get("status") in {"COMPLETED", "FAILED"}

    @staticmethod
    def _build_generation_source(progress: list[dict]) -> dict[str, str]:
        progress_keys = {str(step.get("key") or "") for step in progress}
        if "prepare_context" in progress_keys or "verification_point_extractor" in progress_keys:
            return {
                "entrypoint": "services.question_generation_service.run_question_generation_background_job",
                "service": "QuestionGenerationService.generate_and_store_for_session",
                "graph_runner": "ai.interview_graph_JH.runner.run_interview_question_graph",
                "graph": (
                    "PrepareContext -> VerificationPointExtractor -> Questioner -> "
                    "Predictor -> Driller -> Reviewer -> BuildResponse"
                ),
            }
        return {
            "entrypoint": "services.question_generation_service.run_question_generation_background_job",
            "service": "QuestionGenerationService.generate_and_store_for_session",
            "graph_runner": "ai.interview_graph.runner.run_interview_question_graph",
            "graph": (
                "BuildState -> Analyzer -> Questioner -> Predictor -> Driller -> "
                "Reviewer -> Scorer -> Router -> Selector -> FinalFormatter"
            ),
        }

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
