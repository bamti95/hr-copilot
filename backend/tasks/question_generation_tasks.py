import asyncio
import logging
from typing import Any

from celery import Task

from core.celery_app import celery_app
from core.database import AsyncSessionLocal
from services.question_generation_service import QuestionGenerationService

logger = logging.getLogger(__name__)


class QuestionGenerationTask(Task):
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 300
    retry_jitter = True

    def on_failure(
        self,
        exc: BaseException,
        task_id: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        einfo: Any,
    ) -> None:
        session_id = kwargs.get("session_id") or (args[0] if args else None)
        actor_id = (
            kwargs.get("actor_id")
            if kwargs
            else (args[1] if len(args) > 1 else None)
        )
        if session_id is None:
            logger.error(
                "Question generation task failed without session_id. task_id=%s",
                task_id,
            )
            return

        logger.error(
            "Celery question generation task exhausted retries. session_id=%s task_id=%s",
            session_id,
            task_id,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        asyncio.run(
            _mark_generation_failed(
                session_id=int(session_id),
                actor_id=actor_id,
                reason=str(exc),
            )
        )


@celery_app.task(
    bind=True,
    base=QuestionGenerationTask,
    name="question_generation.generate_for_session",
)
def generate_questions_for_session_task(
    self: QuestionGenerationTask,
    session_id: int,
    actor_id: int | None = None,
) -> dict[str, Any]:
    return asyncio.run(
        _run_generate_questions_for_session(
            session_id=session_id,
            actor_id=actor_id,
        )
    )


async def _run_generate_questions_for_session(
    session_id: int,
    actor_id: int | None,
) -> dict[str, Any]:
    logger.info(
        "Celery question generation task started. session_id=%s actor_id=%s",
        session_id,
        actor_id,
    )
    async with AsyncSessionLocal() as db:
        service = QuestionGenerationService(db)
        result = await service.generate_and_store_for_session(
            session_id=session_id,
            actor_id=actor_id,
            mark_failed_on_error=False,
        )
        logger.info(
            "Celery question generation task completed. session_id=%s status=%s question_count=%s",
            session_id,
            result.status,
            len(result.questions),
        )
        return {
            "session_id": session_id,
            "status": result.status,
            "question_count": len(result.questions),
        }


async def _mark_generation_failed(
    session_id: int,
    actor_id: int | None,
    reason: str,
) -> None:
    async with AsyncSessionLocal() as db:
        service = QuestionGenerationService(db)
        await service.mark_generation_failed(
            session_id=session_id,
            actor_id=actor_id,
            reason=reason,
        )
