import api from "../../../services/api";
import { withLangSmithStyleLlmUsages } from "./llmUsageTrace";
import type {
  LlmCallLog,
  LlmCallLogListResponse,
  LlmUsageCallLog,
  LlmUsageMetric,
  LlmUsageNodeSummary,
  LlmUsageSessionSummary,
  LlmUsageSummaryResponse,
  WorkflowPipelineType,
} from "../types/workflowDashboard.types";

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
  session_id?: number | null;
  candidate_id?: number | null;
  candidate_name?: string | null;
  target_job?: string | null;
  pipeline_type?: string | null;
  target_type?: string | null;
  target_id?: number | null;
  job_posting_id?: number | null;
  job_posting_analysis_report_id?: number | null;
  job_title?: string | null;
  risk_level?: string | null;
  call_count: number;
  total_tokens: number;
  estimated_cost: string | number;
  avg_elapsed_ms: number;
  last_called_at: string | null;
}

interface LlmUsageCallApiResponse {
  id: number;
  session_id?: number | null;
  candidate_id?: number | null;
  candidate_name?: string | null;
  pipeline_type?: string | null;
  target_type?: string | null;
  target_id?: number | null;
  job_posting_id?: number | null;
  job_posting_analysis_report_id?: number | null;
  job_title?: string | null;
  risk_level?: string | null;
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

type JsonRecord = Record<string, unknown>;

interface LlmCallLogApiResponse {
  id: number;
  managerId?: number | null;
  manager_id?: number | null;
  candidateId?: number | null;
  candidate_id?: number | null;
  pipelineType?: string | null;
  pipeline_type?: string | null;
  targetType?: string | null;
  target_type?: string | null;
  targetId?: number | null;
  target_id?: number | null;
  jobPostingId?: number | null;
  job_posting_id?: number | null;
  jobPostingAnalysisReportId?: number | null;
  job_posting_analysis_report_id?: number | null;
  knowledgeSourceId?: number | null;
  knowledge_source_id?: number | null;
  documentId?: number | null;
  document_id?: number | null;
  promptProfileId?: number | null;
  prompt_profile_id?: number | null;
  interviewSessionsId?: number | null;
  interview_sessions_id?: number | null;
  modelName?: string;
  model_name?: string;
  nodeName?: string | null;
  node_name?: string | null;
  runId?: string | null;
  run_id?: string | null;
  parentRunId?: string | null;
  parent_run_id?: string | null;
  traceId?: string | null;
  trace_id?: string | null;
  runType?: string | null;
  run_type?: string | null;
  executionOrder?: number | null;
  execution_order?: number | null;
  requestJson?: JsonRecord | null;
  request_json?: JsonRecord | null;
  outputJson?: JsonRecord | null;
  output_json?: JsonRecord | null;
  responseJson?: JsonRecord | null;
  response_json?: JsonRecord | null;
  inputTokens?: number;
  input_tokens?: number;
  outputTokens?: number;
  output_tokens?: number;
  totalTokens?: number;
  total_tokens?: number;
  estimatedCost?: string | number;
  estimated_cost?: string | number;
  currency: string;
  elapsedMs?: number | null;
  elapsed_ms?: number | null;
  costAmount?: string | number | null;
  cost_amount?: string | number | null;
  callStatus?: string;
  call_status?: string;
  errorMessage?: string | null;
  error_message?: string | null;
  callTime?: number;
  call_time?: number;
  startedAt?: string | null;
  started_at?: string | null;
  endedAt?: string | null;
  ended_at?: string | null;
  createdAt?: string;
  created_at?: string;
}

interface LlmCallLogListApiResponse {
  sessionId?: number;
  session_id?: number;
  traceId?: string | null;
  trace_id?: string | null;
  items: LlmCallLogApiResponse[];
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
    sessionId: response.session_id ?? null,
    candidateId: response.candidate_id ?? null,
    candidateName: response.candidate_name ?? null,
    targetJob: response.target_job ?? null,
    pipelineType: response.pipeline_type ?? undefined,
    targetType: response.target_type ?? null,
    targetId: response.target_id ?? null,
    jobPostingId: response.job_posting_id ?? null,
    jobPostingAnalysisReportId: response.job_posting_analysis_report_id ?? null,
    jobTitle: response.job_title ?? null,
    riskLevel: response.risk_level ?? null,
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
    sessionId: response.session_id ?? null,
    candidateId: response.candidate_id ?? null,
    candidateName: response.candidate_name ?? null,
    pipelineType: response.pipeline_type ?? undefined,
    targetType: response.target_type ?? null,
    targetId: response.target_id ?? null,
    jobPostingId: response.job_posting_id ?? null,
    jobPostingAnalysisReportId: response.job_posting_analysis_report_id ?? null,
    jobTitle: response.job_title ?? null,
    riskLevel: response.risk_level ?? null,
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

function mapWorkflowLog(response: LlmCallLogApiResponse): LlmCallLog {
  return {
    id: response.id,
    managerId: response.managerId ?? response.manager_id ?? null,
    candidateId: response.candidateId ?? response.candidate_id ?? null,
    documentId: response.documentId ?? response.document_id ?? null,
    promptProfileId: response.promptProfileId ?? response.prompt_profile_id ?? null,
    interviewSessionsId:
      response.interviewSessionsId ?? response.interview_sessions_id ?? null,
    pipelineType: response.pipelineType ?? response.pipeline_type ?? undefined,
    targetType: response.targetType ?? response.target_type ?? null,
    targetId: response.targetId ?? response.target_id ?? null,
    jobPostingId: response.jobPostingId ?? response.job_posting_id ?? null,
    jobPostingAnalysisReportId:
      response.jobPostingAnalysisReportId ??
      response.job_posting_analysis_report_id ??
      null,
    knowledgeSourceId:
      response.knowledgeSourceId ?? response.knowledge_source_id ?? null,
    modelName: response.modelName ?? response.model_name ?? "unknown",
    nodeName: response.nodeName ?? response.node_name ?? null,
    runId: response.runId ?? response.run_id ?? null,
    parentRunId: response.parentRunId ?? response.parent_run_id ?? null,
    traceId: response.traceId ?? response.trace_id ?? null,
    runType: response.runType ?? response.run_type ?? null,
    executionOrder: response.executionOrder ?? response.execution_order ?? null,
    requestJson: response.requestJson ?? response.request_json ?? null,
    outputJson: response.outputJson ?? response.output_json ?? null,
    responseJson: response.responseJson ?? response.response_json ?? null,
    inputTokens: response.inputTokens ?? response.input_tokens ?? 0,
    outputTokens: response.outputTokens ?? response.output_tokens ?? 0,
    totalTokens: response.totalTokens ?? response.total_tokens ?? 0,
    estimatedCost: toNumber(response.estimatedCost ?? response.estimated_cost),
    currency: response.currency,
    elapsedMs: response.elapsedMs ?? response.elapsed_ms ?? null,
    costAmount:
      response.costAmount === null || response.cost_amount === null
        ? null
        : toNumber(response.costAmount ?? response.cost_amount),
    callStatus: response.callStatus ?? response.call_status ?? "success",
    errorMessage: response.errorMessage ?? response.error_message ?? null,
    callTime: response.callTime ?? response.call_time ?? 0,
    startedAt: response.startedAt ?? response.started_at ?? null,
    endedAt: response.endedAt ?? response.ended_at ?? null,
    createdAt: response.createdAt ?? response.created_at ?? "",
  };
}

export async function fetchWorkflowSessions(
  pipelineType: WorkflowPipelineType = "INTERVIEW_QUESTION",
): Promise<LlmUsageSummaryResponse> {
  const response = await api.get<ApiEnvelope<LlmUsageSummaryApiResponse>>(
    "/llm-usage/summary",
    { params: { pipelineType } },
  );

  const data = response.data.data;
  return {
    metrics: mapMetric(data.metrics),
    byNode: data.by_node.map(mapNode),
    bySession: data.by_session.map(mapSession),
    recentCalls: data.recent_calls.map(mapCall),
  };
}

export async function fetchSessionLlmLogs(
  sessionId: number,
): Promise<LlmCallLogListResponse> {
  const response = await api.get<LlmCallLogListApiResponse>(
    `/llm-logs/interview-sessions/${sessionId}`,
  );

  return {
    sessionId: response.data.sessionId ?? response.data.session_id ?? sessionId,
    traceId: response.data.traceId ?? response.data.trace_id ?? null,
    items: withLangSmithStyleLlmUsages(response.data.items.map(mapWorkflowLog)),
  };
}

export async function fetchWorkflowExecutionLogs(
  pipelineType: WorkflowPipelineType,
  executionId: number,
): Promise<LlmCallLogListResponse> {
  if (pipelineType === "JOB_POSTING_COMPLIANCE") {
    const response = await api.get<LlmCallLogListApiResponse>(
      `/llm-logs/job-posting-analysis-reports/${executionId}`,
    );

    return {
      sessionId: response.data.sessionId ?? response.data.session_id ?? executionId,
      traceId: response.data.traceId ?? response.data.trace_id ?? null,
      items: withLangSmithStyleLlmUsages(response.data.items.map(mapWorkflowLog)),
    };
  }

  return fetchSessionLlmLogs(executionId);
}
