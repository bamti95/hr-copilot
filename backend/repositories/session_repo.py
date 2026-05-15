"""면접 세션 조회와 진행 상태 갱신 리포지토리.

세션 목록 조회뿐 아니라 질문 생성 파이프라인의 진행 상태도 함께 관리한다.
파이프라인 종류마다 단계 구성이 달라 진행률 규칙을 상수로 분리해 둔다.
"""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.candidate import Candidate
from models.interview_session import InterviewSession
from models.manager import Manager
from repositories.base_repository import BaseRepository


# 기본 질문 생성 파이프라인의 단계 순서다.
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

# JH 파이프라인은 단계 수가 더 적어 별도 진행 규칙을 쓴다.
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
    """UTC 현재 시각을 ISO 문자열로 반환한다."""
    return datetime.now(timezone.utc).isoformat()


def _normalize_graph_impl(graph_impl: str | None) -> str:
    """파이프라인 구현 이름을 내부 키로 정규화한다."""
    normalized = (graph_impl or "default").strip().lower()
    if normalized in QUESTION_GENERATION_PROGRESS_STEPS_BY_PIPELINE:
        return normalized
    return "default"


def _infer_pipeline_from_progress(progress: list[dict] | None) -> str:
    """저장된 progress 구조를 보고 어떤 파이프라인인지 추정한다."""
    keys = {str(step.get("key") or "") for step in (progress or [])}
    if "prepare_context" in keys or "verification_point_extractor" in keys:
        return "jh"
    return "default"


def build_initial_question_generation_progress(graph_impl: str | None = None) -> list[dict]:
    """질문 생성 진행률 초기 구조를 만든다.

    첫 단계만 `PROCESSING`, 나머지는 `PENDING`으로 시작한다.
    """
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
    """면접 세션 조회와 질문 생성 상태 갱신을 담당한다."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, InterviewSession)

    @staticmethod
    def _base_join_stmt():
        """세션 목록 공통 조인 구문을 만든다.

        후보자 이름과 생성자 이름을 함께 조회해 화면에서 바로 쓸 수 있게 한다.
        """
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
        """세션 목록 공통 필터를 적용한다."""
        if candidate_id is not None:
            stmt = stmt.where(InterviewSession.candidate_id == candidate_id)
        if target_job and target_job.strip():
            stmt = stmt.where(InterviewSession.target_job.ilike(f"%{target_job.strip()}%"))
        return stmt

    async def find_by_id_not_deleted(self, session_id: int) -> InterviewSession | None:
        """삭제되지 않은 세션 1건을 조회한다."""
        stmt = select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_id_any(self, session_id: int) -> InterviewSession | None:
        """삭제 여부와 관계없이 세션 1건을 조회한다."""
        stmt = select(InterviewSession).where(InterviewSession.id == session_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_question_generation_queued(
        self,
        session: InterviewSession,
        graph_impl: str | None = None,
    ) -> None:
        """질문 생성을 대기 상태로 바꾸고 진행률을 초기화한다."""
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
        """질문 생성 시작 상태로 갱신한다."""
        session.question_generation_status = "PROCESSING"
        session.question_generation_error = None

    async def mark_question_generation_progress_node(
        self,
        session: InterviewSession,
        node_key: str,
        status: str = "COMPLETED",
        error: str | None = None,
    ) -> None:
        """진행률의 특정 노드 상태를 갱신한다.

        완료된 노드의 다음 단계는 선행 조건을 만족할 때만 `PROCESSING`으로 올린다.
        실패 시에는 다른 진행 중 단계들을 다시 `PENDING`으로 되돌려 흐름을 정리한다.
        """
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
        """질문 생성 전체 완료 상태를 반영한다.

        성공 계열 상태면 남은 진행 단계를 모두 완료 처리한다.
        실패면 마지막 진행 중 단계만 실패로 남긴다.
        """
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
        """세션 상세를 후보자 이름과 생성자 이름까지 포함해 조회한다."""
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
        """필터 조건에 맞는 세션 수를 계산한다."""
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
        """세션 목록을 후보자/생성자 이름과 함께 페이지 조회한다."""
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
