import api from "../../../../services/api";
import type {
  LlmUsageCallLog,
  LlmUsageMetric,
  LlmUsageNodeSummary,
  LlmUsageSessionSummary,
  LlmUsageSummaryResponse,
} from "../types";

interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  message: string;
}

interface LlmUsageMetricApiResponse {
  total_calls: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_tokens: number;
  estimated_cost: string | number;
  avg_elapsed_ms: number;
  failed_calls: number;
}

interface LlmUsageNodeApiResponse {
  node_name: string;
  call_count: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  estimated_cost: string | number;
  avg_elapsed_ms: number;
  failed_calls: number;
}

interface LlmUsageSessionApiResponse {
  session_id: number;
  candidate_id: number;
  candidate_name: string;
  target_job: string;
  call_count: number;
  total_tokens: number;
  estimated_cost: string | number;
  avg_elapsed_ms: number;
  last_called_at: string | null;
}

interface LlmUsageCallApiResponse {
  id: number;
  session_id: number;
  candidate_id: number;
  candidate_name: string;
  node_name: string | null;
  model_name: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  estimated_cost: string | number;
  currency: string;
  elapsed_ms: number | null;
  call_status: string;
  error_message: string | null;
  created_at: string;
}

interface LlmUsageSummaryApiResponse {
  metrics: LlmUsageMetricApiResponse;
  by_node: LlmUsageNodeApiResponse[];
  by_session: LlmUsageSessionApiResponse[];
  recent_calls: LlmUsageCallApiResponse[];
}

function toNumber(value: string | number | null | undefined): number {
  return Number(value ?? 0);
}

function mapMetric(response: LlmUsageMetricApiResponse): LlmUsageMetric {
  return {
    totalCalls: response.total_calls,
    totalInputTokens: response.total_input_tokens,
    totalOutputTokens: response.total_output_tokens,
    totalTokens: response.total_tokens,
    estimatedCost: toNumber(response.estimated_cost),
    avgElapsedMs: response.avg_elapsed_ms,
    failedCalls: response.failed_calls,
  };
}

function mapNode(response: LlmUsageNodeApiResponse): LlmUsageNodeSummary {
  return {
    nodeName: response.node_name,
    callCount: response.call_count,
    inputTokens: response.input_tokens,
    outputTokens: response.output_tokens,
    totalTokens: response.total_tokens,
    estimatedCost: toNumber(response.estimated_cost),
    avgElapsedMs: response.avg_elapsed_ms,
    failedCalls: response.failed_calls,
  };
}

function mapSession(response: LlmUsageSessionApiResponse): LlmUsageSessionSummary {
  return {
    sessionId: response.session_id,
    candidateId: response.candidate_id,
    candidateName: response.candidate_name,
    targetJob: response.target_job,
    callCount: response.call_count,
    totalTokens: response.total_tokens,
    estimatedCost: toNumber(response.estimated_cost),
    avgElapsedMs: response.avg_elapsed_ms,
    lastCalledAt: response.last_called_at,
  };
}

function mapCall(response: LlmUsageCallApiResponse): LlmUsageCallLog {
  return {
    id: response.id,
    sessionId: response.session_id,
    candidateId: response.candidate_id,
    candidateName: response.candidate_name,
    nodeName: response.node_name,
    modelName: response.model_name,
    inputTokens: response.input_tokens,
    outputTokens: response.output_tokens,
    totalTokens: response.total_tokens,
    estimatedCost: toNumber(response.estimated_cost),
    currency: response.currency,
    elapsedMs: response.elapsed_ms,
    callStatus: response.call_status,
    errorMessage: response.error_message,
    createdAt: response.created_at,
  };
}

export async function fetchLlmUsageSummary(): Promise<LlmUsageSummaryResponse> {
  const response = await api.get<ApiEnvelope<LlmUsageSummaryApiResponse>>(
    "/llm-usage/summary",
    { skipGlobalLoading: true },
  );

  const data = response.data.data;
  return {
    metrics: mapMetric(data.metrics),
    byNode: data.by_node.map(mapNode),
    bySession: data.by_session.map(mapSession),
    recentCalls: data.recent_calls.map(mapCall),
  };
}
