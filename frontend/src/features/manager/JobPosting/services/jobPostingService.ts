import api from "../../../../services/api";
import type {
  EvidenceSource,
  JobPostingAiJob,
  JobPostingAnalysisReport,
  JobPostingAnalyzeResponse,
  JobPostingCreateRequest,
  JobPostingIssue,
  JobPostingListResponse,
  JobPostingResponse,
  KnowledgeChunk,
  KnowledgeSearchResponse,
  KnowledgeSearchResult,
  KnowledgeSource,
  KnowledgeSourceListResponse,
} from "../types";

interface ApiEnvelope<T> {
  success?: boolean;
  data?: T;
  message?: string;
}

type JsonRecord = Record<string, unknown>;

interface JobPostingApiResponse {
  id: number;
  input_source: string;
  source_platform: string | null;
  external_posting_id: string | null;
  external_url: string | null;
  company_name: string | null;
  job_title: string;
  target_job: string | null;
  career_level: string | null;
  location: string | null;
  employment_type: string | null;
  salary_text: string | null;
  posting_text: string;
  posting_text_hash: string;
  raw_payload: JsonRecord | null;
  normalized_payload: JsonRecord | null;
  posting_status: string;
  created_at: string;
  updated_at: string;
}

interface JobPostingListApiResponse {
  items: JobPostingApiResponse[];
  total_count: number;
  total_pages: number;
}

interface JobPostingReportApiResponse {
  id: number;
  job_posting_id: number;
  analysis_status: string;
  analysis_type: string;
  analysis_version: string | null;
  model_name: string | null;
  risk_level: string | null;
  issue_count: number;
  violation_count: number;
  warning_count: number;
  confidence_score: number | null;
  detected_issue_types: unknown[] | null;
  retrieval_summary: JsonRecord | null;
  prompt_version: string | null;
  pipeline_version: string | null;
  summary_text: string | null;
  parsed_sections: JsonRecord | null;
  overall_score: number | null;
  risk_score: number | null;
  attractiveness_score: number | null;
  issue_summary: unknown;
  matched_evidence: unknown;
  compliance_warnings: unknown;
  improvement_suggestions: unknown;
  rewrite_examples: unknown;
  final_report: JsonRecord | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

interface JobPostingAnalyzeApiResponse {
  job_posting: JobPostingApiResponse;
  report: JobPostingReportApiResponse;
}

interface JobPostingAiJobApiResponse {
  job_id: number;
  status: string;
  job_type: string;
  target_type: string | null;
  target_id: number | null;
  progress: number;
  current_step: string | null;
  error_message: string | null;
  request_payload: JsonRecord | null;
  result_payload: JsonRecord | null;
  message: string;
}

interface KnowledgeSourceApiResponse {
  id: number;
  source_type: string;
  title: string;
  source_name: string | null;
  source_url: string | null;
  version_label: string | null;
  file_path: string | null;
  file_ext: string | null;
  mime_type: string | null;
  file_size: number | null;
  extract_status: string;
  index_status: string;
  chunk_count: number;
  metadata: JsonRecord | null;
  created_at: string;
  updated_at: string;
}

interface KnowledgeSourceListApiResponse {
  items: KnowledgeSourceApiResponse[];
  total_count: number;
  total_pages: number;
}

interface KnowledgeChunkApiResponse {
  id: number;
  knowledge_source_id: number;
  chunk_type: string;
  chunk_key: string | null;
  chunk_index: number;
  page_start: number | null;
  page_end: number | null;
  section_title: string | null;
  content: string;
  summary: string | null;
  issue_code: string | null;
  risk_category: string | null;
  severity: string | null;
  law_name: string | null;
  article_no: string | null;
  penalty_guide: string | null;
  tags: unknown[] | null;
  metadata: JsonRecord | null;
  embedding_model: string | null;
  content_hash: string;
  token_count: number | null;
}

interface KnowledgeChunkListApiResponse {
  items: KnowledgeChunkApiResponse[];
  total_count: number;
}

interface KnowledgeIndexApiResponse {
  source: KnowledgeSourceApiResponse;
  chunk_count: number;
}

interface KnowledgeSeedApiResponse {
  indexed_sources: KnowledgeSourceApiResponse[];
  total_sources: number;
  total_chunks: number;
}

interface KnowledgeSearchResultApiResponse {
  chunk: KnowledgeChunkApiResponse;
  keyword_score: number;
  vector_score: number;
  hybrid_score: number;
  matched_terms: string[];
}

interface KnowledgeSearchApiResponse {
  query: string;
  search_mode: string;
  embedding_model: string;
  result_count: number;
  results: KnowledgeSearchResultApiResponse[];
}

function unwrap<T>(payload: T | ApiEnvelope<T>): T {
  if (
    payload &&
    typeof payload === "object" &&
    "data" in payload &&
    (payload as ApiEnvelope<T>).data !== undefined
  ) {
    return (payload as ApiEnvelope<T>).data as T;
  }
  return payload as T;
}

function toArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

function toRecord(value: unknown): JsonRecord {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as JsonRecord)
    : {};
}

function mapEvidence(value: unknown): EvidenceSource {
  const item = toRecord(value);
  const textScore = numberOrNull(item.text_score ?? item.textScore);
  const vectorScore = numberOrNull(item.vector_score ?? item.vectorScore);
  const keywordScore = numberOrNull(item.keyword_score ?? item.keywordScore);
  const hybridScore = numberOrNull(item.hybrid_score ?? item.hybridScore);
  const rerankScore = numberOrNull(item.rerank_score ?? item.rerankScore);
  return {
    chunkId: Number(item.chunk_id ?? item.chunkId ?? 0) || undefined,
    sourceId: Number(item.source_id ?? item.sourceId ?? 0) || undefined,
    docId: (item.doc_id as string | null | undefined) ?? (item.docId as string | null | undefined) ?? null,
    title: (item.title as string | null | undefined) ?? null,
    sourceType: (item.source_type as string | null | undefined) ?? null,
    chunkType: (item.chunk_type as string | null | undefined) ?? null,
    sectionTitle: (item.section_title as string | null | undefined) ?? null,
    pageStart:
      typeof item.page_start === "number"
        ? item.page_start
        : typeof item.pageStart === "number"
          ? item.pageStart
          : null,
    pageEnd:
      typeof item.page_end === "number"
        ? item.page_end
        : typeof item.pageEnd === "number"
          ? item.pageEnd
          : null,
    lawName: (item.law_name as string | null | undefined) ?? null,
    articleNo: (item.article_no as string | null | undefined) ?? null,
    articleRef:
      (item.article_ref as string | null | undefined) ??
      (item.articleRef as string | null | undefined) ??
      null,
    effectiveDate:
      (item.effective_date as string | null | undefined) ??
      (item.effectiveDate as string | null | undefined) ??
      null,
    isLatest:
      typeof item.is_latest === "boolean"
        ? item.is_latest
        : typeof item.isLatest === "boolean"
          ? item.isLatest
          : null,
    content: (item.content as string | null | undefined) ?? null,
    score: numberOrNull(item.score) ?? rerankScore ?? hybridScore,
    textScore,
    vectorScore,
    keywordScore,
    hybridScore,
    rerankScore,
    matchedTerms: toArray<string>(item.matched_terms ?? item.matchedTerms),
  };
}

function numberOrNull(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function mapIssue(value: unknown): JobPostingIssue {
  const item = toRecord(value);
  return {
    issueType: String(item.issue_type ?? item.issueType ?? ""),
    severity: String(item.severity ?? ""),
    category: String(item.category ?? ""),
    flaggedText: String(item.flagged_text ?? item.flaggedText ?? ""),
    whyRisky: String(item.why_risky ?? item.whyRisky ?? ""),
    recommendedRevision: String(
      item.recommended_revision ?? item.recommendedRevision ?? "",
    ),
    confidence:
      typeof item.confidence === "number" ? item.confidence : undefined,
    sources: toArray<unknown>(item.sources).map(mapEvidence),
    relatedLaws: toArray<Record<string, unknown>>(
      item.related_laws ?? item.relatedLaws,
    ),
    possiblePenalty:
      (item.possible_penalty as string | null | undefined) ??
      (item.possiblePenalty as string | null | undefined) ??
      null,
  };
}

function mapImprovementSuggestion(value: unknown) {
  const item = toRecord(value);
  return {
    issueType: String(item.issue_type ?? item.issueType ?? ""),
    flaggedText: String(item.flagged_text ?? item.flaggedText ?? ""),
    recommendedRevision: String(
      item.recommended_revision ?? item.recommendedRevision ?? "",
    ),
    evidenceStrength: String(item.evidence_strength ?? item.evidenceStrength ?? ""),
  };
}

function mapPosting(response: JobPostingApiResponse): JobPostingResponse {
  return {
    id: response.id,
    inputSource: response.input_source,
    sourcePlatform: response.source_platform,
    externalPostingId: response.external_posting_id,
    externalUrl: response.external_url,
    companyName: response.company_name,
    jobTitle: response.job_title,
    targetJob: response.target_job,
    careerLevel: response.career_level,
    location: response.location,
    employmentType: response.employment_type,
    salaryText: response.salary_text,
    postingText: response.posting_text,
    postingTextHash: response.posting_text_hash,
    rawPayload: response.raw_payload,
    normalizedPayload: response.normalized_payload,
    postingStatus: response.posting_status,
    createdAt: response.created_at,
    updatedAt: response.updated_at,
  };
}

function mapKnowledgeSource(response: KnowledgeSourceApiResponse): KnowledgeSource {
  return {
    id: response.id,
    sourceType: response.source_type,
    title: response.title,
    sourceName: response.source_name,
    sourceUrl: response.source_url,
    versionLabel: response.version_label,
    filePath: response.file_path,
    fileExt: response.file_ext,
    mimeType: response.mime_type,
    fileSize: response.file_size,
    extractStatus: response.extract_status,
    indexStatus: response.index_status,
    chunkCount: response.chunk_count,
    metadata: response.metadata,
    createdAt: response.created_at,
    updatedAt: response.updated_at,
  };
}

function mapKnowledgeChunk(response: KnowledgeChunkApiResponse): KnowledgeChunk {
  return {
    id: response.id,
    knowledgeSourceId: response.knowledge_source_id,
    chunkType: response.chunk_type,
    chunkKey: response.chunk_key,
    chunkIndex: response.chunk_index,
    pageStart: response.page_start,
    pageEnd: response.page_end,
    sectionTitle: response.section_title,
    content: response.content,
    summary: response.summary,
    issueCode: response.issue_code,
    riskCategory: response.risk_category,
    severity: response.severity,
    lawName: response.law_name,
    articleNo: response.article_no,
    penaltyGuide: response.penalty_guide,
    tags: response.tags,
    metadata: response.metadata,
    embeddingModel: response.embedding_model,
    contentHash: response.content_hash,
    tokenCount: response.token_count,
  };
}

function mapKnowledgeSearchResult(
  response: KnowledgeSearchResultApiResponse,
): KnowledgeSearchResult {
  return {
    chunk: mapKnowledgeChunk(response.chunk),
    keywordScore: response.keyword_score,
    vectorScore: response.vector_score,
    hybridScore: response.hybrid_score,
    matchedTerms: response.matched_terms,
  };
}

function mapAiJob(response: JobPostingAiJobApiResponse): JobPostingAiJob {
  return {
    jobId: response.job_id,
    status: response.status,
    jobType: response.job_type,
    targetType: response.target_type,
    targetId: response.target_id,
    progress: response.progress,
    currentStep: response.current_step,
    errorMessage: response.error_message,
    requestPayload: response.request_payload,
    resultPayload: response.result_payload,
    message: response.message,
  };
}

function mapReport(response: JobPostingReportApiResponse): JobPostingAnalysisReport {
  return {
    id: response.id,
    jobPostingId: response.job_posting_id,
    analysisStatus: response.analysis_status,
    analysisType: response.analysis_type,
    analysisVersion: response.analysis_version,
    modelName: response.model_name,
    riskLevel: response.risk_level,
    issueCount: response.issue_count,
    violationCount: response.violation_count,
    warningCount: response.warning_count,
    confidenceScore: response.confidence_score,
    detectedIssueTypes: response.detected_issue_types,
    retrievalSummary: response.retrieval_summary,
    promptVersion: response.prompt_version,
    pipelineVersion: response.pipeline_version,
    summaryText: response.summary_text,
    parsedSections: response.parsed_sections,
    overallScore: response.overall_score,
    riskScore: response.risk_score,
    attractivenessScore: response.attractiveness_score,
    issueSummary: Array.isArray(response.issue_summary)
      ? response.issue_summary.map(mapIssue)
      : (response.issue_summary as Record<string, unknown> | null),
    matchedEvidence: Array.isArray(response.matched_evidence)
      ? response.matched_evidence.map(mapEvidence)
      : (response.matched_evidence as Record<string, unknown> | null),
    complianceWarnings: Array.isArray(response.compliance_warnings)
      ? response.compliance_warnings.map(mapIssue)
      : (response.compliance_warnings as Record<string, unknown> | null),
    improvementSuggestions: Array.isArray(response.improvement_suggestions)
      ? response.improvement_suggestions.map(mapImprovementSuggestion)
      : (response.improvement_suggestions as Record<string, unknown> | null),
    rewriteExamples: response.rewrite_examples as
      | unknown[]
      | Record<string, unknown>
      | null,
    finalReport: response.final_report,
    errorMessage: response.error_message,
    startedAt: response.started_at,
    completedAt: response.completed_at,
    createdAt: response.created_at,
    updatedAt: response.updated_at,
  };
}

function toRequestPayload(request: JobPostingCreateRequest) {
  return {
    input_source: "MANUAL",
    company_name: request.companyName || null,
    job_title: request.jobTitle,
    target_job: request.targetJob || null,
    career_level: request.careerLevel || null,
    location: request.location || null,
    employment_type: request.employmentType || null,
    salary_text: request.salaryText || null,
    posting_text: request.postingText,
    analysis_type: request.analysisType ?? "FULL",
  };
}

export async function fetchJobPostings(params: {
  page: number;
  size: number;
  keyword?: string;
}): Promise<JobPostingListResponse> {
  const response = await api.get<JobPostingListApiResponse | ApiEnvelope<JobPostingListApiResponse>>(
    "/job-postings",
    {
      params: {
        page: params.page,
        size: params.size,
        keyword: params.keyword || undefined,
      },
    },
  );
  const data = unwrap(response.data);
  return {
    items: data.items.map(mapPosting),
    totalCount: data.total_count,
    totalPages: data.total_pages,
  };
}

export async function fetchJobPosting(postingId: number): Promise<JobPostingResponse> {
  const response = await api.get<JobPostingApiResponse | ApiEnvelope<JobPostingApiResponse>>(
    `/job-postings/${postingId}`,
  );
  return mapPosting(unwrap(response.data));
}

export async function analyzeJobPostingText(
  request: JobPostingCreateRequest,
): Promise<JobPostingAnalyzeResponse> {
  const response = await api.post<
    JobPostingAnalyzeApiResponse | ApiEnvelope<JobPostingAnalyzeApiResponse>
  >("/job-postings/analyze-text", toRequestPayload(request));
  const data = unwrap(response.data);
  return {
    jobPosting: mapPosting(data.job_posting),
    report: mapReport(data.report),
  };
}

export async function submitAnalyzeTextJob(
  request: JobPostingCreateRequest,
): Promise<JobPostingAiJob> {
  const response = await api.post<
    JobPostingAiJobApiResponse | ApiEnvelope<JobPostingAiJobApiResponse>
  >("/job-postings/analyze-text/jobs", toRequestPayload(request), {
    skipGlobalLoading: true,
  });
  return mapAiJob(unwrap(response.data));
}

export async function analyzeJobPostingFile(params: {
  file: File;
  jobTitle?: string;
  companyName?: string;
}): Promise<JobPostingAnalyzeResponse> {
  const formData = new FormData();
  formData.append("file", params.file);
  if (params.jobTitle) formData.append("job_title", params.jobTitle);
  if (params.companyName) formData.append("company_name", params.companyName);

  const response = await api.post<
    JobPostingAnalyzeApiResponse | ApiEnvelope<JobPostingAnalyzeApiResponse>
  >("/job-postings/analyze-file", formData);
  const data = unwrap(response.data);
  return {
    jobPosting: mapPosting(data.job_posting),
    report: mapReport(data.report),
  };
}

export async function submitAnalyzeFileJob(params: {
  file: File;
  jobTitle?: string;
  companyName?: string;
}): Promise<JobPostingAiJob> {
  const formData = new FormData();
  formData.append("file", params.file);
  if (params.jobTitle) formData.append("job_title", params.jobTitle);
  if (params.companyName) formData.append("company_name", params.companyName);

  const response = await api.post<
    JobPostingAiJobApiResponse | ApiEnvelope<JobPostingAiJobApiResponse>
  >("/job-postings/analyze-file/jobs", formData, {
    skipGlobalLoading: true,
  });
  return mapAiJob(unwrap(response.data));
}

export async function analyzeExistingJobPosting(
  postingId: number,
): Promise<JobPostingAnalysisReport> {
  const response = await api.post<
    JobPostingReportApiResponse | ApiEnvelope<JobPostingReportApiResponse>
  >(`/job-postings/${postingId}/analysis-reports`, null, {
    params: { analysis_type: "FULL" },
  });
  return mapReport(unwrap(response.data));
}

export async function submitExistingAnalysisJob(
  postingId: number,
): Promise<JobPostingAiJob> {
  const response = await api.post<
    JobPostingAiJobApiResponse | ApiEnvelope<JobPostingAiJobApiResponse>
  >(`/job-postings/${postingId}/analysis-reports/jobs`, null, {
    params: { analysis_type: "FULL" },
    skipGlobalLoading: true,
  });
  return mapAiJob(unwrap(response.data));
}

export async function fetchAnalysisJob(jobId: number): Promise<JobPostingAiJob> {
  const response = await api.get<
    JobPostingAiJobApiResponse | ApiEnvelope<JobPostingAiJobApiResponse>
  >(`/job-postings/analysis-jobs/${jobId}`, {
    skipGlobalLoading: true,
  });
  return mapAiJob(unwrap(response.data));
}

export async function fetchActiveAnalysisJob(
  postingId?: number,
): Promise<JobPostingAiJob | null> {
  const response = await api.get<
    JobPostingAiJobApiResponse | null | ApiEnvelope<JobPostingAiJobApiResponse | null>
  >("/job-postings/analysis-jobs/active", {
    params: { posting_id: postingId || undefined },
    skipGlobalLoading: true,
  });
  const data = unwrap(response.data);
  return data ? mapAiJob(data) : null;
}

export async function fetchJobPostingReports(
  postingId: number,
): Promise<JobPostingAnalysisReport[]> {
  const response = await api.get<
    JobPostingReportApiResponse[] | ApiEnvelope<JobPostingReportApiResponse[]>
  >(`/job-postings/${postingId}/analysis-reports`, {
    params: { limit: 20 },
  });
  return unwrap(response.data).map(mapReport);
}

export async function fetchJobPostingReport(
  reportId: number,
): Promise<JobPostingAnalysisReport> {
  const response = await api.get<
    JobPostingReportApiResponse | ApiEnvelope<JobPostingReportApiResponse>
  >(`/job-postings/analysis-reports/${reportId}`);
  return mapReport(unwrap(response.data));
}

export async function fetchKnowledgeSources(params: {
  page: number;
  size: number;
  keyword?: string;
}): Promise<KnowledgeSourceListResponse> {
  const response = await api.get<
    KnowledgeSourceListApiResponse | ApiEnvelope<KnowledgeSourceListApiResponse>
  >("/job-postings/knowledge-sources", {
    params: {
      page: params.page,
      size: params.size,
      keyword: params.keyword || undefined,
    },
    skipGlobalLoading: true,
  });
  const data = unwrap(response.data);
  return {
    items: data.items.map(mapKnowledgeSource),
    totalCount: data.total_count,
    totalPages: data.total_pages,
  };
}

export async function uploadKnowledgeSource(params: {
  file: File;
  title?: string;
  sourceType?: string;
  versionLabel?: string;
}): Promise<KnowledgeSource> {
  const formData = new FormData();
  formData.append("file", params.file);
  if (params.title) formData.append("title", params.title);
  if (params.sourceType) formData.append("source_type", params.sourceType);
  if (params.versionLabel) formData.append("version_label", params.versionLabel);

  const response = await api.post<
    KnowledgeSourceApiResponse | ApiEnvelope<KnowledgeSourceApiResponse>
  >("/job-postings/knowledge-sources/upload", formData, {
    skipGlobalLoading: true,
  });
  return mapKnowledgeSource(unwrap(response.data));
}

export async function indexKnowledgeSource(sourceId: number): Promise<{
  source: KnowledgeSource;
  chunkCount: number;
}> {
  const response = await api.post<
    KnowledgeIndexApiResponse | ApiEnvelope<KnowledgeIndexApiResponse>
  >(`/job-postings/knowledge-sources/${sourceId}/index`);
  const data = unwrap(response.data);
  return {
    source: mapKnowledgeSource(data.source),
    chunkCount: data.chunk_count,
  };
}

export async function submitKnowledgeIndexJob(
  sourceId: number,
): Promise<JobPostingAiJob> {
  const response = await api.post<
    JobPostingAiJobApiResponse | ApiEnvelope<JobPostingAiJobApiResponse>
  >(`/job-postings/knowledge-sources/${sourceId}/index/jobs`, null, {
    skipGlobalLoading: true,
  });
  return mapAiJob(unwrap(response.data));
}

export async function seedSourceData(): Promise<{
  indexedSources: KnowledgeSource[];
  totalSources: number;
  totalChunks: number;
}> {
  const response = await api.post<
    KnowledgeSeedApiResponse | ApiEnvelope<KnowledgeSeedApiResponse>
  >("/job-postings/knowledge-sources/seed-source-data");
  const data = unwrap(response.data);
  return {
    indexedSources: data.indexed_sources.map(mapKnowledgeSource),
    totalSources: data.total_sources,
    totalChunks: data.total_chunks,
  };
}

export async function submitSeedSourceDataJob(): Promise<JobPostingAiJob> {
  const response = await api.post<
    JobPostingAiJobApiResponse | ApiEnvelope<JobPostingAiJobApiResponse>
  >("/job-postings/knowledge-sources/seed-source-data/jobs", null, {
    skipGlobalLoading: true,
  });
  return mapAiJob(unwrap(response.data));
}

export async function fetchKnowledgeIndexJob(jobId: number): Promise<JobPostingAiJob> {
  const response = await api.get<
    JobPostingAiJobApiResponse | ApiEnvelope<JobPostingAiJobApiResponse>
  >(`/job-postings/knowledge-index-jobs/${jobId}`, {
    skipGlobalLoading: true,
  });
  return mapAiJob(unwrap(response.data));
}

export async function fetchActiveKnowledgeIndexJob(): Promise<JobPostingAiJob | null> {
  const response = await api.get<
    JobPostingAiJobApiResponse | null | ApiEnvelope<JobPostingAiJobApiResponse | null>
  >("/job-postings/knowledge-index-jobs/active", {
    skipGlobalLoading: true,
  });
  const data = unwrap(response.data);
  return data ? mapAiJob(data) : null;
}

export async function fetchKnowledgeChunks(
  sourceId: number,
): Promise<KnowledgeChunk[]> {
  const response = await api.get<
    KnowledgeChunkListApiResponse | ApiEnvelope<KnowledgeChunkListApiResponse>
  >(`/job-postings/knowledge-sources/${sourceId}/chunks`, {
    params: { limit: 20 },
    skipGlobalLoading: true,
  });
  return unwrap(response.data).items.map(mapKnowledgeChunk);
}

export async function searchKnowledgeSources(params: {
  query: string;
  searchMode: "HYBRID" | "KEYWORD" | "VECTOR";
  limit?: number;
}): Promise<KnowledgeSearchResponse> {
  const response = await api.post<
    KnowledgeSearchApiResponse | ApiEnvelope<KnowledgeSearchApiResponse>
  >("/job-postings/knowledge-sources/search", {
    query: params.query,
    search_mode: params.searchMode,
    limit: params.limit ?? 10,
  });
  const data = unwrap(response.data);
  return {
    query: data.query,
    searchMode: data.search_mode,
    embeddingModel: data.embedding_model,
    resultCount: data.result_count,
    results: data.results.map(mapKnowledgeSearchResult),
  };
}
