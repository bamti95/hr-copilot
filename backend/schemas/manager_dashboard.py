"""관리자 대시보드 응답 스키마를 정의한다."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class DashboardKpis(BaseModel):
    today_todo_count: int
    document_analyzed_count: int
    question_pending_count: int
    review_required_count: int


class DashboardTodoItem(BaseModel):
    type: str
    label: str
    count: int
    target_path: str


class DashboardPipelineItem(BaseModel):
    key: str
    label: str
    count: int


class DashboardPriorityCandidate(BaseModel):
    candidate_id: int
    session_id: int | None = None
    candidate_name: str
    target_job: str | None = None
    priority: str
    status: str
    reason: str
    updated_at: datetime | None = None
    target_path: str


class DashboardRecentSession(BaseModel):
    session_id: int
    candidate_id: int
    candidate_name: str
    target_job: str
    status: str
    question_count: int
    created_at: datetime
    target_path: str


class DashboardRecentActivity(BaseModel):
    id: str
    type: str
    title: str
    description: str
    occurred_at: datetime
    target_path: str


class DashboardLlmCostNode(BaseModel):
    node_name: str
    call_count: int
    total_tokens: int
    estimated_cost: Decimal
    avg_elapsed_ms: float


class DashboardLlmCostSummary(BaseModel):
    today_cost: Decimal = Decimal("0")
    month_cost: Decimal = Decimal("0")
    today_calls: int = 0
    today_failed_calls: int = 0
    today_tokens: int = 0
    avg_elapsed_ms: float = 0
    top_cost_node: DashboardLlmCostNode | None = None
    top_nodes: list[DashboardLlmCostNode] = []


class DashboardJobPostingReportItem(BaseModel):
    report_id: int
    job_posting_id: int
    job_title: str
    company_name: str | None = None
    status: str
    risk_level: str | None = None
    issue_count: int
    violation_count: int
    warning_count: int
    updated_at: datetime | None = None
    target_path: str


class DashboardJobPostingSummary(BaseModel):
    total_postings: int = 0
    analyzed_count: int = 0
    pending_analysis_count: int = 0
    failed_analysis_count: int = 0
    review_required_count: int = 0
    knowledge_sources_count: int = 0
    indexed_knowledge_sources_count: int = 0
    today_cost: Decimal = Decimal("0")
    month_cost: Decimal = Decimal("0")
    estimated_next_analysis_cost: Decimal = Decimal("0")
    projected_today_cost: Decimal = Decimal("0")
    recent_reports: list[DashboardJobPostingReportItem] = []


class ManagerDashboardSummaryData(BaseModel):
    kpis: DashboardKpis
    todos: list[DashboardTodoItem]
    pipeline: list[DashboardPipelineItem]
    llm_cost: DashboardLlmCostSummary
    job_posting: DashboardJobPostingSummary
    priority_candidates: list[DashboardPriorityCandidate]
    recent_sessions: list[DashboardRecentSession]
    recent_activities: list[DashboardRecentActivity]


class ManagerDashboardSummaryResponse(BaseModel):
    success: bool = True
    data: ManagerDashboardSummaryData
    message: str

