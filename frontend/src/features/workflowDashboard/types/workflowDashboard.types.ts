export type WorkflowPipelineType =
  | "INTERVIEW_QUESTION"
  | "JOB_POSTING_COMPLIANCE";

export interface WorkflowPipelineOption {
  value: WorkflowPipelineType;
  label: string;
  description: string;
}

export const workflowPipelineOptions: WorkflowPipelineOption[] = [
  {
    value: "INTERVIEW_QUESTION",
    label: "질문 생성",
    description: "면접 질문 생성 LangGraph 실행 흐름",
  },
  {
    value: "JOB_POSTING_COMPLIANCE",
    label: "채용공고 점검",
    description: "Agentic RAG 기반 채용공고 컴플라이언스 흐름",
  },
];

export interface LlmUsageMetric {
  totalCalls: number;
  totalInputTokens: number;
  totalOutputTokens: number;
  totalTokens: number;
  estimatedCost: number;
  avgElapsedMs: number;
  failedCalls: number;
}

export interface LlmUsageNodeSummary {
  nodeName: string;
  callCount: number;
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  estimatedCost: number;
  avgElapsedMs: number;
  failedCalls: number;
}

export interface LlmUsageSessionSummary {
  sessionId: number | null;
  candidateId: number | null;
  candidateName: string | null;
  targetJob: string | null;
  pipelineType?: WorkflowPipelineType | string;
  targetType?: string | null;
  targetId?: number | null;
  jobPostingId?: number | null;
  jobPostingAnalysisReportId?: number | null;
  jobTitle?: string | null;
  riskLevel?: string | null;
  callCount: number;
  totalTokens: number;
  estimatedCost: number;
  avgElapsedMs: number;
  lastCalledAt: string | null;
}

export interface LlmUsageCallLog {
  id: number;
  sessionId: number | null;
  candidateId: number | null;
  candidateName: string | null;
  pipelineType?: WorkflowPipelineType | string;
  targetType?: string | null;
  targetId?: number | null;
  jobPostingId?: number | null;
  jobPostingAnalysisReportId?: number | null;
  jobTitle?: string | null;
  riskLevel?: string | null;
  nodeName: string | null;
  modelName: string;
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  estimatedCost: number;
  currency: string;
  elapsedMs: number | null;
  callStatus: string;
  errorMessage: string | null;
  createdAt: string;
}

export interface LlmUsageSummaryResponse {
  metrics: LlmUsageMetric;
  byNode: LlmUsageNodeSummary[];
  bySession: LlmUsageSessionSummary[];
  recentCalls: LlmUsageCallLog[];
}

export interface LlmCallLog {
  id: number;
  managerId: number | null;
  candidateId: number | null;
  documentId: number | null;
  promptProfileId: number | null;
  interviewSessionsId: number | null;
  pipelineType?: WorkflowPipelineType | string;
  targetType?: string | null;
  targetId?: number | null;
  jobPostingId?: number | null;
  jobPostingAnalysisReportId?: number | null;
  knowledgeSourceId?: number | null;
  modelName: string;
  nodeName: string | null;
  runId: string | null;
  parentRunId: string | null;
  traceId: string | null;
  runType: string | null;
  executionOrder: number | null;
  requestJson: Record<string, unknown> | null;
  outputJson: Record<string, unknown> | null;
  responseJson: Record<string, unknown> | null;
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  estimatedCost: number;
  currency: string;
  elapsedMs: number | null;
  costAmount: number | null;
  callStatus: string;
  errorMessage: string | null;
  callTime: number;
  startedAt: string | null;
  endedAt: string | null;
  createdAt: string;
}

export interface LlmCallLogListResponse {
  sessionId: number | null;
  traceId: string | null;
  items: LlmCallLog[];
}

export type DetailTab =
  | "feedback"
  | "input"
  | "output"
  | "state"
  | "router"
  | "meta";
export type SessionFilter = "all" | "success" | "failed";
export type SessionSort = "recent" | "latency" | "cost" | "tokens";

export const emptyWorkflowSummary: LlmUsageSummaryResponse = {
  metrics: {
    totalCalls: 0,
    totalInputTokens: 0,
    totalOutputTokens: 0,
    totalTokens: 0,
    estimatedCost: 0,
    avgElapsedMs: 0,
    failedCalls: 0,
  },
  byNode: [],
  bySession: [],
  recentCalls: [],
};

export function getWorkflowExecutionId(
  session: LlmUsageSessionSummary,
): number | null {
  return (
    session.sessionId ??
    session.jobPostingAnalysisReportId ??
    session.targetId ??
    null
  );
}

export function getCallExecutionId(call: LlmUsageCallLog): number | null {
  return (
    call.sessionId ??
    call.jobPostingAnalysisReportId ??
    call.targetId ??
    null
  );
}

export function getWorkflowExecutionTitle(
  session: LlmUsageSessionSummary,
): string {
  return (
    session.candidateName ??
    session.jobTitle ??
    session.targetJob ??
    `Execution #${getWorkflowExecutionId(session) ?? "-"}`
  );
}

export function getWorkflowExecutionSubtitle(
  session: LlmUsageSessionSummary,
): string {
  if (session.pipelineType === "JOB_POSTING_COMPLIANCE") {
    return `${session.riskLevel ?? "RISK"} · ${session.jobTitle ?? session.targetJob ?? "채용공고"}`;
  }
  return session.targetJob ?? "면접 질문 생성";
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("ko-KR").format(value);
}

export function formatCost(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 4,
    maximumFractionDigits: 6,
  }).format(value);
}

export function formatMs(value: number | null | undefined): string {
  if (value === null || value === undefined) return "-";
  if (value >= 1000) return `${(value / 1000).toFixed(2)}초`;
  return `${Math.round(value)}ms`;
}

export function formatDateTime(value: string | null): string {
  if (!value) return "-";
  return new Intl.DateTimeFormat("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function normalizeStatus(status: string | null | undefined): string {
  const value = (status ?? "").toLowerCase();
  if (value.includes("fail") || value.includes("error")) return "failed";
  if (value.includes("retry")) return "retry";
  if (value.includes("skip")) return "skipped";
  if (value.includes("running")) return "running";
  return "success";
}

export function statusLabel(status: string | null | undefined): string {
  const normalized = normalizeStatus(status);
  if (normalized === "failed") return "실패";
  if (normalized === "retry") return "재시도";
  if (normalized === "running") return "실행중";
  if (normalized === "skipped") return "건너뜀";
  return "성공";
}

export function statusClasses(status: string | null | undefined): string {
  const normalized = normalizeStatus(status);
  if (normalized === "failed") return "border-rose-200 bg-rose-50 text-rose-700";
  if (normalized === "retry") return "border-amber-200 bg-amber-50 text-amber-700";
  if (normalized === "running") return "border-sky-200 bg-sky-50 text-sky-700";
  if (normalized === "skipped") return "border-slate-200 bg-slate-50 text-slate-500";
  return "border-emerald-200 bg-emerald-50 text-emerald-700";
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function getArray(
  value: Record<string, unknown> | null,
  key: string,
): unknown[] {
  const nested = value?.[key];
  return Array.isArray(nested) ? nested : [];
}

export function getNestedRecord(
  value: Record<string, unknown> | null,
  key: string,
): Record<string, unknown> | null {
  const nested = value?.[key];
  return isRecord(nested) ? nested : null;
}

export function getFinalResponse(logs: LlmCallLog[]): Record<string, unknown> | null {
  const finalLog = [...logs]
    .reverse()
    .find(
      (log) =>
        log.nodeName === "final_formatter" ||
        log.nodeName === "finalize_report" ||
        log.outputJson?.final_response,
    );
  const finalResponse = finalLog?.outputJson?.final_response;
  if (isRecord(finalResponse)) return finalResponse;
  return finalLog?.outputJson ?? null;
}
