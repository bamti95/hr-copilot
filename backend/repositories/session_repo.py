from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.candidate import Candidate
from models.interview_session import InterviewSession
from models.manager import Manager
from repositories.base_repository import BaseRepository


DEFAULT_QUESTION_GENERATION_PROGRESS_STEPS = [
    ("build_state", "Input Build"),
    ("analyzer", "Document Analysis"),
    ("questioner", "Question Generation"),
    ("selector_lite", "Initial Selection"),
    ("predictor", "Predicted Answer"),
    ("driller", "Follow-up Question"),
    ("reviewer", "Question Review"),
    ("scorer", "Question Scoring"),
    ("selector", "Final Selection"),
    ("final_formatter", "Result Formatting"),
]

JH_QUESTION_GENERATION_PROGRESS_STEPS = [
    ("prepare_context", "Context Preparation"),
    ("verification_point_extractor", "Verification Point Extraction"),
    ("questioner", "Question Generation"),
    ("predictor", "Predicted Answer"),
    ("driller", "Follow-up Question"),
    ("reviewer", "Question Review"),
]

QUESTION_GENERATION_PROGRESS_STEPS_BY_PIPELINE = {
    "default": DEFAULT_QUESTION_GENERATION_PROGRESS_STEPS,
    "hy": DEFAULT_QUESTION_GENERATION_PROGRESS_STEPS,
    "jy": DEFAULT_QUESTION_GENERATION_PROGRESS_STEPS,
    "jh": JH_QUESTION_GENERATION_PROGRESS_STEPS,
}

DEFAULT_LINEAR_NEXT_PROGRESS_STEP = {
    "build_state": ["analyzer"],
    "analyzer": ["questioner"],
    "questioner": ["selector_lite"],
    "selector_lite": ["predictor"],
    "predictor": ["driller"],
    "driller": ["reviewer"],
    "reviewer": ["scorer"],
    "scorer": ["selector"],
    "selector": ["final_formatter"],
}

JH_LINEAR_NEXT_PROGRESS_STEP = {
    "prepare_context": ["verification_point_extractor"],
    "verification_point_extractor": ["questioner"],
    "questioner": ["predictor"],
    "predictor": ["driller"],
    "driller": ["reviewer"],
}

LINEAR_NEXT_PROGRESS_STEP_BY_PIPELINE = {
    "default": DEFAULT_LINEAR_NEXT_PROGRESS_STEP,
    "hy": DEFAULT_LINEAR_NEXT_PROGRESS_STEP,
    "jy": DEFAULT_LINEAR_NEXT_PROGRESS_STEP,
    "jh": JH_LINEAR_NEXT_PROGRESS_STEP,
}

DEFAULT_PROGRESS_STEP_PREREQUISITES = {
    "scorer": {"predictor", "driller", "reviewer"},
    "selector": {"scorer"},
    "final_formatter": {"selector"},
}

PROGRESS_STEP_PREREQUISITES_BY_PIPELINE = {
    "default": DEFAULT_PROGRESS_STEP_PREREQUISITES,
    "hy": DEFAULT_PROGRESS_STEP_PREREQUISITES,
    "jy": DEFAULT_PROGRESS_STEP_PREREQUISITES,
    "jh": {},
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_graph_impl(graph_impl: str | None) -> str:
    normalized = (graph_impl or "default").strip().lower()
    if normalized in QUESTION_GENERATION_PROGRESS_STEPS_BY_PIPELINE:
        return normalized
    return "default"


def _infer_pipeline_from_progress(progress: list[dict] | None) -> str:
    keys = {str(step.get("key") or "") for step in (progress or [])}
    if "prepare_context" in keys or "verification_point_extractor" in keys:
        return "jh"
    return "default"


def build_initial_question_generation_progress(graph_impl: str | None = None) -> list[dict]:
    pipeline = _normalize_graph_impl(graph_impl)
    steps = []
    for index, (key, label) in enumerate(
        QUESTION_GENERATION_PROGRESS_STEPS_BY_PIPELINE[pipeline]
    ):
        steps.append(
            {
                "key": key,
                "label": label,
                "status": "PROCESSING" if index == 0 else "PENDING",
                "started_at": _now_iso() if index == 0 else None,
                "completed_at": None,
                "attempt": 0,
            }
        )
    return steps


class SessionRepository(BaseRepository[InterviewSession]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, InterviewSession)

    @staticmethod
    def _base_join_stmt():
        return (
            select(
                InterviewSession,
                Candidate.name.label("candidate_name"),
                Manager.name.label("created_name"),
            )
            .join(
                Candidate,
                InterviewSession.candidate_id == Candidate.id,
            )
            .outerjoin(
                Manager,
                InterviewSession.created_by == Manager.id,
            )
            .where(
                InterviewSession.deleted_at.is_(None),
                Candidate.deleted_at.is_(None),
            )
        )

    @staticmethod
    def _apply_filters(stmt, candidate_id: int | None, target_job: str | None):
        if candidate_id is not None:
            stmt = stmt.where(InterviewSession.candidate_id == candidate_id)
        if target_job and target_job.strip():
            stmt = stmt.where(InterviewSession.target_job.ilike(f"%{target_job.strip()}%"))
        return stmt

    async def find_by_id_not_deleted(self, session_id: int) -> InterviewSession | None:
        stmt = select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_id_any(self, session_id: int) -> InterviewSession | None:
        stmt = select(InterviewSession).where(InterviewSession.id == session_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_question_generation_queued(
        self,
        session: InterviewSession,
        graph_impl: str | None = None,
    ) -> None:
        session.question_generation_status = "QUEUED"
        session.question_generation_error = None
        session.question_generation_requested_at = datetime.now(timezone.utc)
        session.question_generation_completed_at = None
        session.question_generation_progress = build_initial_question_generation_progress(
            graph_impl
        )

    async def mark_question_generation_processing(
        self,
        session: InterviewSession,
    ) -> None:
        session.question_generation_status = "PROCESSING"
        session.question_generation_error = None

    async def mark_question_generation_progress_node(
        self,
        session: InterviewSession,
        node_key: str,
        status: str = "COMPLETED",
        error: str | None = None,
    ) -> None:
        progress = list(
            session.question_generation_progress
            or build_initial_question_generation_progress()
        )
        if not any(step.get("key") == node_key for step in progress):
            return

        pipeline = _infer_pipeline_from_progress(progress)
        next_step_map = LINEAR_NEXT_PROGRESS_STEP_BY_PIPELINE[pipeline]
        prerequisites_map = PROGRESS_STEP_PREREQUISITES_BY_PIPELINE[pipeline]
        now = _now_iso()

        for index, step in enumerate(progress):
            if step.get("key") == node_key:
                attempt = int(step.get("attempt") or 0)
                step["status"] = status
                step["completed_at"] = now if status in {"COMPLETED", "FAILED"} else None
                step["started_at"] = step.get("started_at") or now
                step["attempt"] = attempt + 1 if status == "COMPLETED" else attempt
                if error:
                    step["error"] = error

                next_keys = set(next_step_map.get(node_key, []))
                completed_keys = {
                    item.get("key")
                    for item in progress
                    if item.get("status") == "COMPLETED"
                }
                for next_step in progress[index + 1 :]:
                    next_key = next_step.get("key")
                    prerequisites = prerequisites_map.get(next_key, set())
                    if (
                        next_key in next_keys
                        and next_step.get("status") == "PENDING"
                        and prerequisites.issubset(completed_keys)
                    ):
                        next_step["status"] = "PROCESSING"
                        next_step["started_at"] = next_step.get("started_at") or now
                break

        if status == "FAILED":
            for step in progress:
                if step.get("status") == "PROCESSING" and step.get("key") != node_key:
                    step["status"] = "PENDING"

        session.question_generation_progress = progress

    async def mark_question_generation_completed(
        self,
        session: InterviewSession,
        status: str,
        error: str | None = None,
        *,
        refresh_completed_timestamp: bool = True,
    ) -> None:
        session.question_generation_status = status
        session.question_generation_error = error
        if refresh_completed_timestamp or session.question_generation_completed_at is None:
            session.question_generation_completed_at = datetime.now(timezone.utc)
        if status in {"COMPLETED", "PARTIAL_COMPLETED"}:
            progress = list(session.question_generation_progress or [])
            now = _now_iso()
            for step in progress:
                if step.get("status") != "FAILED":
                    step["started_at"] = step.get("started_at") or now
                    step["status"] = "COMPLETED"
                    step["completed_at"] = step.get("completed_at") or now
            session.question_generation_progress = progress
        elif status == "FAILED":
            progress = list(session.question_generation_progress or [])
            now = _now_iso()
            for step in progress:
                if step.get("status") == "PROCESSING":
                    step["status"] = "FAILED"
                    step["completed_at"] = now
                    if error:
                        step["error"] = error
                    break
            session.question_generation_progress = progress

    async def get_detail_with_candidate(self, session_id: int) -> InterviewSession | None:
        stmt = self._base_join_stmt().where(InterviewSession.id == session_id)
        result = await self.db.execute(stmt)
        row = result.one_or_none()
        if row is None:
            return None

        session, candidate_name, created_name = row
        setattr(session, "candidate_name", candidate_name)
        setattr(session, "created_name", created_name)
        return session

    async def count_list(
        self,
        candidate_id: int | None = None,
        target_job: str | None = None,
    ) -> int:
        stmt = (
            select(func.count(InterviewSession.id))
            .select_from(InterviewSession)
            .join(Candidate, InterviewSession.candidate_id == Candidate.id)
            .where(
                InterviewSession.deleted_at.is_(None),
                Candidate.deleted_at.is_(None),
            )
        )
        stmt = self._apply_filters(stmt, candidate_id, target_job)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def find_list(
        self,
        page: int,
        limit: int,
        candidate_id: int | None = None,
        target_job: str | None = None,
    ) -> list[InterviewSession]:
        offset = (page - 1) * limit
        stmt = self._base_join_stmt().order_by(InterviewSession.id.desc()).offset(offset).limit(limit)
        stmt = self._apply_filters(stmt, candidate_id, target_job)
        result = await self.db.execute(stmt)

        sessions: list[InterviewSession] = []
        for session, candidate_name, created_name in result.all():
            setattr(session, "candidate_name", candidate_name)
            setattr(session, "created_name", created_name)
            sessions.append(session)
        return sessions
