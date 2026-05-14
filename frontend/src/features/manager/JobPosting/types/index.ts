export type JobPostingRiskLevel =
  | "CLEAN"
  | "LOW"
  | "MEDIUM"
  | "HIGH"
  | "CRITICAL"
  | string;

export interface JobPostingResponse {
  id: number;
  inputSource: string;
  sourcePlatform: string | null;
  externalPostingId: string | null;
  externalUrl: string | null;
  companyName: string | null;
  jobTitle: string;
  targetJob: string | null;
  careerLevel: string | null;
  location: string | null;
  employmentType: string | null;
  salaryText: string | null;
  postingText: string;
  postingTextHash: string;
  rawPayload: Record<string, unknown> | null;
  normalizedPayload: Record<string, unknown> | null;
  postingStatus: string;
  createdAt: string;
  updatedAt: string;
}

export interface JobPostingListResponse {
  items: JobPostingResponse[];
  totalCount: number;
  totalPages: number;
}

export interface JobPostingCreateRequest {
  companyName?: string | null;
  jobTitle: string;
  targetJob?: string | null;
  careerLevel?: string | null;
  location?: string | null;
  employmentType?: string | null;
  salaryText?: string | null;
  postingText: string;
  analysisType?: string;
}

export interface EvidenceSource {
  chunkId?: number;
  sourceId?: number;
  docId?: string | null;
  title?: string | null;
  sourceType?: string | null;
  chunkType?: string | null;
  sectionTitle?: string | null;
  pageStart?: number | null;
  pageEnd?: number | null;
  lawName?: string | null;
  articleNo?: string | null;
  articleRef?: string | null;
  effectiveDate?: string | null;
  isLatest?: boolean | null;
  content?: string | null;
  score?: number | null;
  textScore?: number | null;
  vectorScore?: number | null;
  keywordScore?: number | null;
  hybridScore?: number | null;
  rerankScore?: number | null;
  matchedTerms?: string[];
}

export interface JobPostingIssue {
  issueType?: string;
  severity?: string;
  category?: string;
  flaggedText?: string;
  whyRisky?: string;
  recommendedRevision?: string;
  confidence?: number;
  sources?: EvidenceSource[];
  relatedLaws?: Array<Record<string, unknown>>;
  possiblePenalty?: string | null;
}

export interface JobPostingImprovementSuggestion {
  issueType?: string;
  flaggedText?: string;
  recommendedRevision?: string;
  evidenceStrength?: string;
}

export interface JobPostingAnalysisReport {
  id: number;
  jobPostingId: number;
  analysisStatus: string;
  analysisType: string;
  analysisVersion: string | null;
  modelName: string | null;
  riskLevel: JobPostingRiskLevel | null;
  issueCount: number;
  violationCount: number;
  warningCount: number;
  confidenceScore: number | null;
  detectedIssueTypes: unknown[] | null;
  retrievalSummary: Record<string, unknown> | null;
  promptVersion: string | null;
  pipelineVersion: string | null;
  summaryText: string | null;
  parsedSections: Record<string, unknown> | null;
  overallScore: number | null;
  riskScore: number | null;
  attractivenessScore: number | null;
  issueSummary: JobPostingIssue[] | Record<string, unknown> | null;
  matchedEvidence: EvidenceSource[] | Record<string, unknown> | null;
  complianceWarnings: JobPostingIssue[] | Record<string, unknown> | null;
  improvementSuggestions:
    | JobPostingImprovementSuggestion[]
    | Record<string, unknown>
    | null;
  rewriteExamples: unknown[] | Record<string, unknown> | null;
  finalReport: Record<string, unknown> | null;
  errorMessage: string | null;
  startedAt: string | null;
  completedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface JobPostingAnalyzeResponse {
  jobPosting: JobPostingResponse;
  report: JobPostingAnalysisReport;
}

export interface JobPostingAiJob {
  jobId: number;
  status: string;
  jobType: string;
  targetType: string | null;
  targetId: number | null;
  progress: number;
  currentStep: string | null;
  errorMessage: string | null;
  requestPayload: Record<string, unknown> | null;
  resultPayload: Record<string, unknown> | null;
  message: string;
}

export interface KnowledgeSource {
  id: number;
  sourceType: string;
  title: string;
  sourceName: string | null;
  sourceUrl: string | null;
  versionLabel: string | null;
  filePath: string | null;
  fileExt: string | null;
  mimeType: string | null;
  fileSize: number | null;
  extractStatus: string;
  indexStatus: string;
  chunkCount: number;
  metadata: Record<string, unknown> | null;
  createdAt: string;
  updatedAt: string;
}

export interface KnowledgeSourceListResponse {
  items: KnowledgeSource[];
  totalCount: number;
  totalPages: number;
}

export interface KnowledgeChunk {
  id: number;
  knowledgeSourceId: number;
  chunkType: string;
  chunkKey: string | null;
  chunkIndex: number;
  pageStart: number | null;
  pageEnd: number | null;
  sectionTitle: string | null;
  content: string;
  summary: string | null;
  issueCode: string | null;
  riskCategory: string | null;
  severity: string | null;
  lawName: string | null;
  articleNo: string | null;
  penaltyGuide: string | null;
  tags: unknown[] | null;
  metadata: Record<string, unknown> | null;
  embeddingModel: string | null;
  contentHash: string;
  tokenCount: number | null;
}

export interface KnowledgeSearchResult {
  chunk: KnowledgeChunk;
  keywordScore: number;
  vectorScore: number;
  hybridScore: number;
  matchedTerms: string[];
}

export interface KnowledgeSearchResponse {
  query: string;
  searchMode: string;
  embeddingModel: string;
  resultCount: number;
  results: KnowledgeSearchResult[];
}
