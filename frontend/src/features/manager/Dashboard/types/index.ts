export interface DashboardKpis {
  todayTodoCount: number;
  documentAnalyzedCount: number;
  questionPendingCount: number;
  reviewRequiredCount: number;
}

export interface DashboardTodoItem {
  type: string;
  label: string;
  count: number;
  targetPath: string;
}

export interface DashboardPipelineItem {
  key: string;
  label: string;
  count: number;
}

export interface DashboardLlmCostNode {
  nodeName: string;
  callCount: number;
  totalTokens: number;
  estimatedCost: number;
  avgElapsedMs: number;
}

export interface DashboardLlmCostSummary {
  todayCost: number;
  monthCost: number;
  todayCalls: number;
  todayFailedCalls: number;
  todayTokens: number;
  avgElapsedMs: number;
  topCostNode: DashboardLlmCostNode | null;
  topNodes: DashboardLlmCostNode[];
}

export type DashboardPriority = "HIGH" | "MEDIUM" | "LOW";

export interface DashboardPriorityCandidate {
  candidateId: number;
  sessionId: number | null;
  candidateName: string;
  targetJob: string | null;
  priority: DashboardPriority;
  status: string;
  reason: string;
  updatedAt: string | null;
  targetPath: string;
}

export interface DashboardRecentSession {
  sessionId: number;
  candidateId: number;
  candidateName: string;
  targetJob: string;
  status: string;
  questionCount: number;
  createdAt: string;
  targetPath: string;
}

export interface DashboardRecentActivity {
  id: string;
  type: string;
  title: string;
  description: string;
  occurredAt: string;
  targetPath: string;
}

export interface DashboardSummary {
  kpis: DashboardKpis;
  todos: DashboardTodoItem[];
  pipeline: DashboardPipelineItem[];
  llmCost: DashboardLlmCostSummary;
  priorityCandidates: DashboardPriorityCandidate[];
  recentSessions: DashboardRecentSession[];
  recentActivities: DashboardRecentActivity[];
}

export const emptyDashboardSummary: DashboardSummary = {
  kpis: {
    todayTodoCount: 0,
    documentAnalyzedCount: 0,
    questionPendingCount: 0,
    reviewRequiredCount: 0,
  },
  todos: [],
  pipeline: [],
  llmCost: {
    todayCost: 0,
    monthCost: 0,
    todayCalls: 0,
    todayFailedCalls: 0,
    todayTokens: 0,
    avgElapsedMs: 0,
    topCostNode: null,
    topNodes: [],
  },
  priorityCandidates: [],
  recentSessions: [],
  recentActivities: [],
};

export function formatDashboardNumber(value: number): string {
  return new Intl.NumberFormat("ko-KR").format(value);
}

export function formatDashboardCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: value > 0 && value < 0.01 ? 4 : 2,
    maximumFractionDigits: value > 0 && value < 0.01 ? 6 : 2,
  }).format(value);
}

export function formatDashboardSeconds(value: number): string {
  if (!Number.isFinite(value) || value <= 0) return "-";
  return `${(value / 1000).toFixed(1)}초`;
}

export function formatDashboardDateTime(value: string | null): string {
  if (!value) return "-";
  return new Intl.DateTimeFormat("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    NOT_REQUESTED: "미요청",
    QUEUED: "대기",
    PROCESSING: "생성 중",
    COMPLETED: "완료",
    PARTIAL_COMPLETED: "일부 완료",
    FAILED: "실패",
  };
  return labels[status] ?? status;
}

export function statusClasses(status: string): string {
  if (status === "FAILED" || status === "실패" || status.includes("반려")) {
    return "border-rose-200 bg-rose-50 text-rose-700";
  }
  if (
    status === "PARTIAL_COMPLETED" ||
    status === "일부 완료" ||
    status.includes("검토") ||
    status.includes("수정")
  ) {
    return "border-amber-200 bg-amber-50 text-amber-700";
  }
  if (status === "PROCESSING" || status === "QUEUED" || status.includes("대기")) {
    return "border-sky-200 bg-sky-50 text-sky-700";
  }
  return "border-emerald-200 bg-emerald-50 text-emerald-700";
}

export function priorityLabel(priority: DashboardPriority): string {
  if (priority === "HIGH") return "높음";
  if (priority === "MEDIUM") return "중간";
  return "낮음";
}

export function priorityClasses(priority: DashboardPriority): string {
  if (priority === "HIGH") return "border-rose-200 bg-rose-50 text-rose-700";
  if (priority === "MEDIUM") return "border-amber-200 bg-amber-50 text-amber-700";
  return "border-slate-200 bg-slate-50 text-slate-600";
}
