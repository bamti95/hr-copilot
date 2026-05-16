"""관리자 대시보드 요약 데이터를 만든다.

지원자, 문서, 면접 세션, LLM 사용량을 한 화면에서 볼 수 있도록
여러 저장소의 집계 값을 모아 대시보드 전용 응답으로 조합한다.
우선순위 후보와 최근 활동은 운영자가 바로 확인할 대상을
빠르게 찾게 하는 데 목적이 있다.
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.manager_dashboard_repository import (
    PENDING_QUESTION_STATUSES,
    ManagerDashboardRepository,
)
from schemas.manager_dashboard import (
    DashboardKpis,
    DashboardJobPostingReportItem,
    DashboardJobPostingSummary,
    DashboardLlmCostNode,
    DashboardLlmCostSummary,
    DashboardPipelineItem,
    DashboardPriorityCandidate,
    DashboardRecentActivity,
    DashboardRecentSession,
    DashboardTodoItem,
    ManagerDashboardSummaryData,
    ManagerDashboardSummaryResponse,
)


def _int_value(value: object) -> int:
    """집계 결과의 null 값을 0으로 보정한다."""
    return int(value or 0)


def _float_value(value: object) -> float:
    """평균 시간 같은 집계 수치를 실수로 변환한다."""
    return float(value or 0)


def _decimal_value(value: object) -> Decimal:
    """비용 수치를 Decimal로 변환한다."""
    return Decimal(str(value or 0))


def _session_path(session_id: int) -> str:
    """세션 상세 화면 경로를 만든다."""
    return f"/manager/interview-sessions/{session_id}"


def _candidate_path(candidate_id: int) -> str:
    """지원자 상세 화면 경로를 만든다."""
    return f"/manager/candidates/{candidate_id}"


def _status_label(status: str | None) -> str:
    """대시보드 표시용 상태 라벨을 반환한다."""
    labels = {
        "NOT_REQUESTED": "미요청",
        "QUEUED": "대기",
        "PROCESSING": "생성 중",
        "COMPLETED": "완료",
        "PARTIAL_COMPLETED": "일부 완료",
        "FAILED": "실패",
    }
    return labels.get(status or "", status or "-")


def _priority_rank(priority: str) -> int:
    """우선순위 정렬용 숫자 값을 반환한다."""
    return {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(priority, 3)


class ManagerDashboardService:
    """관리자 홈 대시보드에 필요한 종합 데이터를 구성한다."""

    def __init__(self, db: AsyncSession):
        self.repository = ManagerDashboardRepository(db)

    async def get_summary(self) -> ManagerDashboardSummaryResponse:
        """대시보드 첫 화면에 필요한 모든 요약 정보를 반환한다.

        KPI, 할 일, 파이프라인 현황, 비용, 우선순위 후보, 최근 활동을
        한 번에 구성해 프론트가 추가 계산 없이 바로 그릴 수 있게 한다.
        """
        document_pending_count = await self.repository.count_document_pending()
        document_failed_count = await self.repository.count_document_failed()
        document_analyzed_candidate_count = (
            await self.repository.count_document_analyzed_candidates()
        )
        question_pending_count = await self.repository.count_question_pending_sessions()
        question_failed_count = await self.repository.count_question_failed_sessions()
        partial_session_count = await self.repository.count_partial_sessions()
        review_problem_session_count = (
            await self.repository.count_review_problem_sessions()
        )
        today_todo_count = (
            document_pending_count
            + document_failed_count
            + question_pending_count
            + question_failed_count
            + partial_session_count
            + review_problem_session_count
        )
        review_required_count = (
            question_failed_count + partial_session_count + review_problem_session_count
        )

        candidate_count = await self.repository.count_candidates()
        document_uploaded_candidate_count = (
            await self.repository.count_document_uploaded_candidates()
        )
        session_count = await self.repository.count_sessions()
        question_completed_count = (
            await self.repository.count_question_completed_sessions()
        )
        review_passed_count = await self.repository.count_review_passed_sessions()

        return ManagerDashboardSummaryResponse(
            data=ManagerDashboardSummaryData(
                kpis=DashboardKpis(
                    today_todo_count=today_todo_count,
                    document_analyzed_count=document_analyzed_candidate_count,
                    question_pending_count=question_pending_count,
                    review_required_count=review_required_count,
                ),
                todos=[
                    DashboardTodoItem(
                        type="DOCUMENT_PENDING",
                        label="문서 분석 대기",
                        count=document_pending_count,
                        target_path="/manager/candidates",
                    ),
                    DashboardTodoItem(
                        type="DOCUMENT_FAILED",
                        label="문서 분석 실패",
                        count=document_failed_count,
                        target_path="/manager/candidates",
                    ),
                    DashboardTodoItem(
                        type="QUESTION_PENDING",
                        label="질문 생성 대기",
                        count=question_pending_count,
                        target_path="/manager/interview-sessions",
                    ),
                    DashboardTodoItem(
                        type="QUESTION_FAILED",
                        label="질문 생성 실패",
                        count=question_failed_count,
                        target_path="/manager/interview-sessions",
                    ),
                    DashboardTodoItem(
                        type="PARTIAL_SESSION",
                        label="일부 완료 세션",
                        count=partial_session_count,
                        target_path="/manager/interview-sessions",
                    ),
                    DashboardTodoItem(
                        type="REVIEW_REQUIRED",
                        label="검토 필요 질문",
                        count=review_problem_session_count,
                        target_path="/manager/interview-sessions",
                    ),
                ],
                pipeline=[
                    DashboardPipelineItem(
                        key="candidate_registered",
                        label="지원자 등록",
                        count=candidate_count,
                    ),
                    DashboardPipelineItem(
                        key="document_uploaded",
                        label="문서 업로드",
                        count=document_uploaded_candidate_count,
                    ),
                    DashboardPipelineItem(
                        key="document_analyzed",
                        label="문서 분석 완료",
                        count=document_analyzed_candidate_count,
                    ),
                    DashboardPipelineItem(
                        key="session_created",
                        label="면접 세션 생성",
                        count=session_count,
                    ),
                    DashboardPipelineItem(
                        key="question_generated",
                        label="질문 생성 완료",
                        count=question_completed_count,
                    ),
                    DashboardPipelineItem(
                        key="review_passed",
                        label="검토 통과",
                        count=review_passed_count,
                    ),
                ],
                llm_cost=await self._build_llm_cost_summary(),
                job_posting=await self._build_job_posting_summary(),
                priority_candidates=await self._build_priority_candidates(),
                recent_sessions=await self._build_recent_sessions(),
                recent_activities=await self._build_recent_activities(),
            ),
            message="HR 담당자 대시보드 요약 조회 성공",
        )

    async def _build_llm_cost_summary(self) -> DashboardLlmCostSummary:
        """오늘과 이번 달의 LLM 비용 집계를 구성한다."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        metrics_row = await self.repository.get_llm_cost_metrics_row(
            today_start=today_start,
            month_start=month_start,
        )
        node_rows = await self.repository.get_llm_top_cost_node_rows(
            month_start=month_start,
        )
        top_nodes = [
            DashboardLlmCostNode(
                node_name=row[0],
                call_count=_int_value(row[1]),
                total_tokens=_int_value(row[2]),
                estimated_cost=_decimal_value(row[3]),
                avg_elapsed_ms=_float_value(row[4]),
            )
            for row in node_rows
        ]

        return DashboardLlmCostSummary(
            today_cost=_decimal_value(metrics_row[0]),
            month_cost=_decimal_value(metrics_row[1]),
            today_calls=_int_value(metrics_row[2]),
            today_failed_calls=_int_value(metrics_row[3]),
            today_tokens=_int_value(metrics_row[4]),
            avg_elapsed_ms=_float_value(metrics_row[5]),
            top_cost_node=top_nodes[0] if top_nodes else None,
            top_nodes=top_nodes,
        )

    async def _build_job_posting_summary(self) -> DashboardJobPostingSummary:
        """채용공고 RAG 분석 현황과 관련 비용을 구성한다."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        pending_count = await self.repository.count_job_posting_pending_analysis()
        cost_row = await self.repository.get_job_posting_llm_cost_metrics_row(
            today_start=today_start,
            month_start=month_start,
        )
        today_cost = _decimal_value(cost_row[0])
        estimated_next_cost = _decimal_value(cost_row[2])

        return DashboardJobPostingSummary(
            total_postings=await self.repository.count_job_postings(),
            analyzed_count=await self.repository.count_job_posting_analyzed(),
            pending_analysis_count=pending_count,
            failed_analysis_count=await self.repository.count_job_posting_failed_analysis(),
            review_required_count=await self.repository.count_job_posting_review_required(),
            knowledge_sources_count=await self.repository.count_job_posting_knowledge_sources(),
            indexed_knowledge_sources_count=(
                await self.repository.count_job_posting_indexed_knowledge_sources()
            ),
            today_cost=today_cost,
            month_cost=_decimal_value(cost_row[1]),
            estimated_next_analysis_cost=estimated_next_cost,
            projected_today_cost=today_cost + (estimated_next_cost * pending_count),
            recent_reports=[
                DashboardJobPostingReportItem(
                    report_id=row[0],
                    job_posting_id=row[1],
                    job_title=row[2],
                    company_name=row[3],
                    status=row[4],
                    risk_level=row[5],
                    issue_count=_int_value(row[6]),
                    violation_count=_int_value(row[7]),
                    warning_count=_int_value(row[8]),
                    updated_at=row[9],
                    target_path=f"/manager/job-postings/{row[1]}/report",
                )
                for row in await self.repository.get_recent_job_posting_report_rows()
            ],
        )

    async def _build_priority_candidates(self) -> list[DashboardPriorityCandidate]:
        """지금 먼저 봐야 할 지원자/세션 목록을 만든다.

        실패, 반려, 낮은 점수, 수정 필요 같은 운영 리스크를 우선한다.
        같은 대상이 여러 조건에 걸리면 마지막 상태로 덮지 않고,
        고유 키로 한 번만 남긴 뒤 우선순위와 최신 시각으로 정렬한다.
        """
        rows = await self.repository.get_priority_session_rows()
        items: list[DashboardPriorityCandidate] = []
        for row in rows:
            (
                session_id,
                candidate_id,
                candidate_name,
                target_job,
                generation_status,
                generation_error,
                created_at,
                requested_at,
                completed_at,
                min_score,
                rejected_count,
                needs_revision_count,
            ) = row

            priority: str | None = None
            status = _status_label(generation_status)
            reason = "확인할 이슈가 있습니다."
            if generation_status in {"FAILED", "PARTIAL_COMPLETED"}:
                priority = "HIGH"
                reason = generation_error or "질문 생성이 실패했거나 일부만 완료되었습니다."
            elif _int_value(rejected_count) > 0:
                priority = "HIGH"
                status = "질문 반려"
                reason = "반려된 면접 질문이 포함되어 있습니다."
            elif min_score is not None and int(min_score) < 70:
                priority = "HIGH"
                status = "낮은 점수"
                reason = f"최저 질문 점수가 {int(min_score)}점입니다."
            elif _int_value(needs_revision_count) > 0:
                priority = "MEDIUM"
                status = "수정 필요"
                reason = "수정이 필요한 면접 질문이 포함되어 있습니다."
            elif min_score is not None and int(min_score) < 80:
                priority = "MEDIUM"
                status = "검토 필요"
                reason = f"최저 질문 점수가 {int(min_score)}점입니다."
            elif generation_status in PENDING_QUESTION_STATUSES:
                priority = "LOW"
                reason = "질문 생성이 아직 완료되지 않았습니다."

            if priority is None:
                continue

            updated_at = completed_at or requested_at or created_at
            items.append(
                DashboardPriorityCandidate(
                    candidate_id=candidate_id,
                    session_id=session_id,
                    candidate_name=candidate_name,
                    target_job=target_job,
                    priority=priority,
                    status=status,
                    reason=reason,
                    updated_at=updated_at,
                    target_path=_session_path(session_id),
                )
            )

        for candidate_id, candidate_name, job_position, updated_at in (
            await self.repository.get_candidates_without_session_rows()
        ):
            items.append(
                DashboardPriorityCandidate(
                    candidate_id=candidate_id,
                    session_id=None,
                    candidate_name=candidate_name,
                    target_job=job_position,
                    priority="LOW",
                    status="세션 없음",
                    reason="지원자는 등록되었지만 면접 세션이 아직 생성되지 않았습니다.",
                    updated_at=updated_at,
                    target_path=_candidate_path(candidate_id),
                )
            )

        for candidate_id, candidate_name, job_position, updated_at in (
            await self.repository.get_document_failed_candidate_rows()
        ):
            items.append(
                DashboardPriorityCandidate(
                    candidate_id=candidate_id,
                    session_id=None,
                    candidate_name=candidate_name,
                    target_job=job_position,
                    priority="MEDIUM",
                    status="문서 분석 실패",
                    reason="분석에 실패한 지원자 문서가 있습니다.",
                    updated_at=updated_at,
                    target_path=_candidate_path(candidate_id),
                )
            )

        unique_items: dict[tuple[int, int | None, str], DashboardPriorityCandidate] = {}
        for item in items:
            key = (item.candidate_id, item.session_id, item.status)
            unique_items[key] = item

        return sorted(
            unique_items.values(),
            key=lambda item: (
                _priority_rank(item.priority),
                -(item.updated_at or datetime.min.replace(tzinfo=timezone.utc)).timestamp(),
            ),
        )[:10]

    async def _build_recent_sessions(self) -> list[DashboardRecentSession]:
        """최근 생성되거나 진행된 세션 목록을 반환한다."""
        rows = await self.repository.get_recent_session_rows()
        return [
            DashboardRecentSession(
                session_id=row[0],
                candidate_id=row[1],
                candidate_name=row[2],
                target_job=row[3],
                status=row[4],
                question_count=_int_value(row[5]),
                created_at=row[6],
                target_path=_session_path(row[0]),
            )
            for row in rows
        ]

    async def _build_recent_activities(self) -> list[DashboardRecentActivity]:
        """지원자, 문서, 세션, 질문 단위 최근 활동을 시간순으로 합친다."""
        activities: list[DashboardRecentActivity] = []

        for candidate_id, name, job_position, created_at in (
            await self.repository.get_recent_candidate_activity_rows()
        ):
            activities.append(
                DashboardRecentActivity(
                    id=f"candidate-{candidate_id}",
                    type="CANDIDATE_CREATED",
                    title=f"{name} 지원자 등록",
                    description=job_position or "지원 직무 미지정",
                    occurred_at=created_at,
                    target_path=_candidate_path(candidate_id),
                )
            )

        for document_id, candidate_id, name, title, created_at in (
            await self.repository.get_recent_document_activity_rows()
        ):
            activities.append(
                DashboardRecentActivity(
                    id=f"document-{document_id}",
                    type="DOCUMENT_UPLOADED",
                    title=f"{name} 문서 업로드",
                    description=title,
                    occurred_at=created_at,
                    target_path=f"/manager/candidates/{candidate_id}/documents/{document_id}",
                )
            )

        for row in await self.repository.get_recent_session_activity_rows():
            (
                session_id,
                candidate_id,
                name,
                target_job,
                created_at,
                requested_at,
                completed_at,
                generation_status,
            ) = row
            activities.append(
                DashboardRecentActivity(
                    id=f"session-{session_id}",
                    type="SESSION_CREATED",
                    title=f"{name} 면접 세션 생성",
                    description=target_job,
                    occurred_at=created_at,
                    target_path=_session_path(session_id),
                )
            )
            if requested_at is not None:
                activities.append(
                    DashboardRecentActivity(
                        id=f"session-requested-{session_id}",
                        type="QUESTION_GENERATION_REQUESTED",
                        title=f"{name} 질문 생성 요청",
                        description=_status_label(generation_status),
                        occurred_at=requested_at,
                        target_path=_session_path(session_id),
                    )
                )
            if completed_at is not None:
                activities.append(
                    DashboardRecentActivity(
                        id=f"session-completed-{session_id}",
                        type="QUESTION_GENERATION_COMPLETED",
                        title=f"{name} 질문 생성 {_status_label(generation_status)}",
                        description=target_job,
                        occurred_at=completed_at,
                        target_path=_session_path(session_id),
                    )
                )

        for question_id, session_id, name, category, created_at in (
            await self.repository.get_recent_question_activity_rows()
        ):
            activities.append(
                DashboardRecentActivity(
                    id=f"question-{question_id}",
                    type="QUESTION_CREATED",
                    title=f"{name} 면접 질문 저장",
                    description=category,
                    occurred_at=created_at,
                    target_path=_session_path(session_id),
                )
            )

        return sorted(activities, key=lambda item: item.occurred_at, reverse=True)[:12]
