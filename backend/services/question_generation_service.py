import asyncio
import json
import logging
from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from ai.interview_graph.schemas import InterviewQuestionItem, QuestionGenerationResponse, ReviewResult
from core.config import settings
from core.database import AsyncSessionLocal
from models.interview_question import InterviewQuestion
from repositories.interview_question_repository import InterviewQuestionRepository
from repositories.session_repo import SessionRepository
from schemas.session_generation import (
    CandidateInterviewPrepInput,
    build_candidate_interview_prep_log_payload,
)
from services.session_generation_payload_assembler import SessionGenerationPayloadAssembler

logger = logging.getLogger(__name__)

GraphRunner = Callable[
    [CandidateInterviewPrepInput, Callable[[str], Awaitable[None]] | None],
    Awaitable[QuestionGenerationResponse],
]


def resolve_question_graph_runner(graph_impl: str) -> GraphRunner:
    impl = (graph_impl or "default").strip().lower()
    if impl == "jh":
        from ai.interview_graph_JH.runner import run_interview_question_graph

        return run_interview_question_graph
    if impl == "hy":
        from ai.interview_graph_HY.runner import run_interview_question_graph

        return run_interview_question_graph
    if impl == "jy":
        from ai.interview_graph_JY.runner import run_interview_question_graph

        return run_interview_question_graph
    from ai.interview_graph.runner import run_interview_question_graph as run_default

    return run_default


class QuestionGenerationService:
    def __init__(self, db: AsyncSession | None = None):
        self.db = db
        self.question_repo = InterviewQuestionRepository(db) if db is not None else None
        self.session_repo = SessionRepository(db) if db is not None else None

    async def request_candidate_interview_prep(
        self,
        payload: CandidateInterviewPrepInput,
        on_node_complete: Callable[[str], Awaitable[None]] | None = None,
        *,
        graph_impl: str = "default",
    ) -> QuestionGenerationResponse:
        logger.info(
            "Question Generation Request Payload\n%s",
            json.dumps(
                build_candidate_interview_prep_log_payload(payload),
                ensure_ascii=False,
                indent=2,
            ),
        )

        runner = resolve_question_graph_runner(graph_impl)
        result = await runner(payload, on_node_complete)

        logger.info(
            "Question Generation Completed session_id=%s candidate_id=%s status=%s question_count=%s",
            payload.session.session_id,
            payload.candidate.candidate_id,
            result.status,
            len(result.questions),
        )

        return result

    async def generate_and_store_for_session(
        self,
        session_id: int,
        actor_id: int | None,
        target_question_ids: list[str] | None = None,
        *,
        graph_impl: str = "default",
    ) -> QuestionGenerationResponse:
        if self.db is None or self.question_repo is None or self.session_repo is None:
            raise RuntimeError("QuestionGenerationService requires a database session.")

        session = await self.session_repo.find_by_id_not_deleted(session_id)
        if session is None:
            raise ValueError(f"Interview session not found: {session_id}")

        await self.session_repo.mark_question_generation_processing(session)
        await self.db.commit()

        try:
            requested_question_ids = [
                question_id.strip()
                for question_id in (target_question_ids or [])
                if question_id.strip()
            ]
            active_questions = await self.question_repo.find_active_by_session_id(session_id)
            active_question_ids = {str(question.id) for question in active_questions}
            selected_question_ids = [
                question_id
                for question_id in requested_question_ids
                if question_id in active_question_ids
            ]
            if requested_question_ids and not selected_question_ids:
                raise ValueError("Regeneration target questions were not found.")

            assembler = SessionGenerationPayloadAssembler(self.db)
            payload = await assembler.build_candidate_interview_prep_input(
                session_id,
                manager_id=actor_id,
            )
            if selected_question_ids:
                payload.human_action = "regenerate_question"
                payload.target_question_ids = selected_question_ids
                payload.existing_questions = [
                    self._serialize_existing_question(question)
                    for question in active_questions
                ]
                payload.additional_instruction = (
                    "target_question_ids에 포함된 기존 질문만 새 질문으로 다시 생성하세요. "
                    "선택되지 않은 기존 질문과 중복되지 않도록 하세요."
                )

            async def mark_node_complete(node_name: str) -> None:
                await self.session_repo.mark_question_generation_progress_node(
                    session,
                    node_key=node_name,
                )
                await self.db.commit()

            result = await asyncio.wait_for(
                self.request_candidate_interview_prep(
                    payload,
                    on_node_complete=mark_node_complete,
                    graph_impl=graph_impl,
                ),
                timeout=settings.QUESTION_GENERATION_JOB_TIMEOUT_SECONDS,
            )

            if selected_question_ids:
                if result.status != "failed":
                    await self._update_selected_questions(
                        existing_questions=active_questions,
                        target_question_ids=selected_question_ids,
                        result=result,
                    )
            else:
                await self._replace_stored_questions(
                    session_id=session_id,
                    actor_id=actor_id,
                    result=result,
                )
            final_status = (
                "FAILED"
                if result.status == "failed"
                else "PARTIAL_COMPLETED"
                if result.status == "partial_completed"
                else "COMPLETED"
            )
            await self.session_repo.mark_question_generation_completed(
                session,
                status=final_status,
                error=result.generation_metadata.get("error"),
            )
            await self.db.commit()
            return result
        except Exception as exc:
            await self.db.rollback()
            session = await self.session_repo.find_by_id_not_deleted(session_id)
            if session is not None:
                await self.session_repo.mark_question_generation_completed(
                    session,
                    status="FAILED",
                    error=str(exc),
                )
                await self.db.commit()
            logger.exception(
                "Question generation background job failed session_id=%s",
                session_id,
            )
            raise

    @staticmethod
    def _serialize_existing_question(question: InterviewQuestion) -> dict:
        return {
            "id": str(question.id),
            "category": question.category,
            "question_text": question.question_text,
            "generation_basis": question.question_rationale,
            "document_evidence": question.document_evidence or [],
            "evaluation_guide": question.evaluation_guide,
            "risk_tags": question.risk_tags or [],
            "competency_tags": question.competency_tags or [],
            "review_status": question.review_status,
            "review_reason": question.review_reason,
            "score": question.score,
            "score_reason": question.score_reason,
        }

    @staticmethod
    def _apply_question_item(entity: InterviewQuestion, item: InterviewQuestionItem) -> None:
        review: ReviewResult = item.review
        entity.category = item.category
        entity.question_text = item.question_text
        entity.expected_answer = item.predicted_answer
        entity.expected_answer_basis = item.predicted_answer_basis
        entity.follow_up_question = item.follow_up_question
        entity.follow_up_basis = item.follow_up_basis
        entity.evaluation_guide = item.evaluation_guide
        entity.question_rationale = item.generation_basis
        entity.document_evidence = item.document_evidence
        entity.risk_tags = item.risk_tags
        entity.competency_tags = item.competency_tags
        entity.review_status = review.status
        entity.review_reason = review.reason
        entity.review_reject_reason = review.reject_reason
        entity.review_recommended_revision = review.recommended_revision
        entity.score = item.score
        entity.score_reason = item.score_reason

    async def _update_selected_questions(
        self,
        existing_questions: list[InterviewQuestion],
        target_question_ids: list[str],
        result: QuestionGenerationResponse,
    ) -> None:
        questions_by_id = {
            str(question.id): question
            for question in existing_questions
        }
        for target_question_id, item in zip(target_question_ids, result.questions, strict=False):
            entity = questions_by_id.get(target_question_id)
            if entity is not None:
                self._apply_question_item(entity, item)

    async def _replace_stored_questions(
        self,
        session_id: int,
        actor_id: int | None,
        result: QuestionGenerationResponse,
    ) -> None:
        if self.question_repo is None:
            raise RuntimeError("Question repository is not initialized.")

        await self.question_repo.soft_delete_by_session_id(
            session_id=session_id,
            actor_id=actor_id,
        )
        for item in result.questions:
            review: ReviewResult = item.review
            await self.question_repo.add(
                InterviewQuestion(
                    interview_sessions_id=session_id,
                    category=item.category,
                    question_text=item.question_text,
                    expected_answer=item.predicted_answer,
                    expected_answer_basis=item.predicted_answer_basis,
                    follow_up_question=item.follow_up_question,
                    follow_up_basis=item.follow_up_basis,
                    evaluation_guide=item.evaluation_guide,
                    question_rationale=item.generation_basis,
                    document_evidence=item.document_evidence,
                    risk_tags=item.risk_tags,
                    competency_tags=item.competency_tags,
                    review_status=review.status,
                    review_reason=review.reason,
                    review_reject_reason=review.reject_reason,
                    review_recommended_revision=review.recommended_revision,
                    score=item.score,
                    score_reason=item.score_reason,
                    created_by=actor_id,
                )
            )


async def run_question_generation_background_job(
    session_id: int,
    actor_id: int | None,
    target_question_ids: list[str] | None = None,
    graph_impl: str = "default",
) -> None:
    async with AsyncSessionLocal() as db:
        service = QuestionGenerationService(db)
        await service.generate_and_store_for_session(
            session_id=session_id,
            actor_id=actor_id,
            target_question_ids=target_question_ids,
            graph_impl=graph_impl,
        )
