import asyncio
import json
import logging
from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from ai.interview_graph.runner import run_interview_question_graph
from ai.interview_graph.schemas import QuestionGenerationResponse, ReviewResult
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


class QuestionGenerationService:
    def __init__(self, db: AsyncSession | None = None):
        self.db = db
        self.question_repo = InterviewQuestionRepository(db) if db is not None else None
        self.session_repo = SessionRepository(db) if db is not None else None

    async def request_candidate_interview_prep(
        self,
        payload: CandidateInterviewPrepInput,
        on_node_complete: Callable[[str], Awaitable[None]] | None = None,
    ) -> QuestionGenerationResponse:
        logger.info(
            "Question Generation Request Payload\n%s",
            json.dumps(
                build_candidate_interview_prep_log_payload(payload),
                ensure_ascii=False,
                indent=2,
            ),
        )

        result = await run_interview_question_graph(
            payload,
            on_node_complete=on_node_complete,
        )

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
    ) -> QuestionGenerationResponse:
        if self.db is None or self.question_repo is None or self.session_repo is None:
            raise RuntimeError("QuestionGenerationService requires a database session.")

        session = await self.session_repo.find_by_id_not_deleted(session_id)
        if session is None:
            raise ValueError(f"Interview session not found: {session_id}")

        await self.session_repo.mark_question_generation_processing(session)
        await self.db.commit()

        try:
            assembler = SessionGenerationPayloadAssembler(self.db)
            payload = await assembler.build_candidate_interview_prep_input(session_id)

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
                ),
                timeout=settings.QUESTION_GENERATION_JOB_TIMEOUT_SECONDS,
            )

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
) -> None:
    async with AsyncSessionLocal() as db:
        service = QuestionGenerationService(db)
        await service.generate_and_store_for_session(
            session_id=session_id,
            actor_id=actor_id,
        )
