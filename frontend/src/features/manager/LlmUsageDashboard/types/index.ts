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
  sessionId: number;
  candidateId: number;
  candidateName: string;
  targetJob: string;
  callCount: number;
  totalTokens: number;
  estimatedCost: number;
  avgElapsedMs: number;
  lastCalledAt: string | null;
}

export interface LlmUsageCallLog {
  id: number;
  sessionId: number;
  candidateId: number;
  candidateName: string;
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

export type WorkflowLogStatus = "success" | "failed" | "retry" | "running" | "skipped";

export interface LlmCallLog {
  id: number;
  managerId: number | null;
  candidateId: number;
  documentId: number | null;
  promptProfileId: number | null;
  interviewSessionsId: number;
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
  sessionId: number;
  traceId: string | null;
  items: LlmCallLog[];
}
