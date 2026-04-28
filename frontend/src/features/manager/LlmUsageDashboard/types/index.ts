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
