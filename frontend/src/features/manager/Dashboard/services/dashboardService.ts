import api from "../../../../services/api";
import type {
  DashboardPriority,
  DashboardRecentActivity,
  DashboardRecentSession,
  DashboardSummary,
} from "../types";

interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  message: string;
}

interface DashboardSummaryApiResponse {
  kpis: {
    today_todo_count: number;
    document_analyzed_count: number;
    question_pending_count: number;
    review_required_count: number;
  };
  todos: Array<{
    type: string;
    label: string;
    count: number;
    target_path: string;
  }>;
  pipeline: Array<{
    key: string;
    label: string;
    count: number;
  }>;
  llm_cost: {
    today_cost: string | number;
    month_cost: string | number;
    today_calls: number;
    today_failed_calls: number;
    today_tokens: number;
    avg_elapsed_ms: number;
    top_cost_node: DashboardLlmCostNodeApiResponse | null;
    top_nodes: DashboardLlmCostNodeApiResponse[];
  };
  job_posting: {
    total_postings: number;
    analyzed_count: number;
    pending_analysis_count: number;
    failed_analysis_count: number;
    review_required_count: number;
    knowledge_sources_count: number;
    indexed_knowledge_sources_count: number;
    today_cost: string | number;
    month_cost: string | number;
    estimated_next_analysis_cost: string | number;
    projected_today_cost: string | number;
    recent_reports: Array<{
      report_id: number;
      job_posting_id: number;
      job_title: string;
      company_name: string | null;
      status: string;
      risk_level: string | null;
      issue_count: number;
      violation_count: number;
      warning_count: number;
      updated_at: string | null;
      target_path: string;
    }>;
  };
  priority_candidates: Array<{
    candidate_id: number;
    session_id: number | null;
    candidate_name: string;
    target_job: string | null;
    priority: DashboardPriority;
    status: string;
    reason: string;
    updated_at: string | null;
    target_path: string;
  }>;
  recent_sessions: Array<{
    session_id: number;
    candidate_id: number;
    candidate_name: string;
    target_job: string;
    status: string;
    question_count: number;
    created_at: string;
    target_path: string;
  }>;
  recent_activities: Array<{
    id: string;
    type: string;
    title: string;
    description: string;
    occurred_at: string;
    target_path: string;
  }>;
}

interface DashboardLlmCostNodeApiResponse {
  node_name: string;
  call_count: number;
  total_tokens: number;
  estimated_cost: string | number;
  avg_elapsed_ms: number;
}

function toNumber(value: string | number | null | undefined): number {
  return Number(value ?? 0);
}

function mapLlmCostNode(
  item: DashboardLlmCostNodeApiResponse,
): DashboardSummary["llmCost"]["topNodes"][number] {
  return {
    nodeName: item.node_name,
    callCount: item.call_count,
    totalTokens: item.total_tokens,
    estimatedCost: toNumber(item.estimated_cost),
    avgElapsedMs: item.avg_elapsed_ms,
  };
}

function mapRecentSession(item: DashboardSummaryApiResponse["recent_sessions"][number]): DashboardRecentSession {
  return {
    sessionId: item.session_id,
    candidateId: item.candidate_id,
    candidateName: item.candidate_name,
    targetJob: item.target_job,
    status: item.status,
    questionCount: item.question_count,
    createdAt: item.created_at,
    targetPath: item.target_path,
  };
}

function mapRecentActivity(
  item: DashboardSummaryApiResponse["recent_activities"][number],
): DashboardRecentActivity {
  return {
    id: item.id,
    type: item.type,
    title: item.title,
    description: item.description,
    occurredAt: item.occurred_at,
    targetPath: item.target_path,
  };
}

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const response = await api.get<ApiEnvelope<DashboardSummaryApiResponse>>(
    "/manager/dashboard/summary",
  );
  const data = response.data.data;

  return {
    kpis: {
      todayTodoCount: data.kpis.today_todo_count,
      documentAnalyzedCount: data.kpis.document_analyzed_count,
      questionPendingCount: data.kpis.question_pending_count,
      reviewRequiredCount: data.kpis.review_required_count,
    },
    todos: data.todos.map((item) => ({
      type: item.type,
      label: item.label,
      count: item.count,
      targetPath: item.target_path,
    })),
    pipeline: data.pipeline.map((item) => ({
      key: item.key,
      label: item.label,
      count: item.count,
    })),
    llmCost: {
      todayCost: toNumber(data.llm_cost.today_cost),
      monthCost: toNumber(data.llm_cost.month_cost),
      todayCalls: data.llm_cost.today_calls,
      todayFailedCalls: data.llm_cost.today_failed_calls,
      todayTokens: data.llm_cost.today_tokens,
      avgElapsedMs: data.llm_cost.avg_elapsed_ms,
      topCostNode: data.llm_cost.top_cost_node
        ? mapLlmCostNode(data.llm_cost.top_cost_node)
        : null,
      topNodes: data.llm_cost.top_nodes.map(mapLlmCostNode),
    },
    jobPosting: {
      totalPostings: data.job_posting.total_postings,
      analyzedCount: data.job_posting.analyzed_count,
      pendingAnalysisCount: data.job_posting.pending_analysis_count,
      failedAnalysisCount: data.job_posting.failed_analysis_count,
      reviewRequiredCount: data.job_posting.review_required_count,
      knowledgeSourcesCount: data.job_posting.knowledge_sources_count,
      indexedKnowledgeSourcesCount: data.job_posting.indexed_knowledge_sources_count,
      todayCost: toNumber(data.job_posting.today_cost),
      monthCost: toNumber(data.job_posting.month_cost),
      estimatedNextAnalysisCost: toNumber(
        data.job_posting.estimated_next_analysis_cost,
      ),
      projectedTodayCost: toNumber(data.job_posting.projected_today_cost),
      recentReports: data.job_posting.recent_reports.map((item) => ({
        reportId: item.report_id,
        jobPostingId: item.job_posting_id,
        jobTitle: item.job_title,
        companyName: item.company_name,
        status: item.status,
        riskLevel: item.risk_level,
        issueCount: item.issue_count,
        violationCount: item.violation_count,
        warningCount: item.warning_count,
        updatedAt: item.updated_at,
        targetPath: item.target_path,
      })),
    },
    priorityCandidates: data.priority_candidates.map((item) => ({
      candidateId: item.candidate_id,
      sessionId: item.session_id,
      candidateName: item.candidate_name,
      targetJob: item.target_job,
      priority: item.priority,
      status: item.status,
      reason: item.reason,
      updatedAt: item.updated_at,
      targetPath: item.target_path,
    })),
    recentSessions: data.recent_sessions.map(mapRecentSession),
    recentActivities: data.recent_activities.map(mapRecentActivity),
  };
}
