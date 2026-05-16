import type { PagedListResponse } from "../../../../common/types/pagination";
import type { InterviewSessionGraphPipeline } from "../../InterviewSession/types";

export type CandidateApplyStatus =
  | "APPLIED"
  | "SCREENING"
  | "INTERVIEW"
  | "ACCEPTED"
  | "REJECTED";

export const CANDIDATE_APPLY_STATUS_LABEL: Record<CandidateApplyStatus, string> = {
  APPLIED: "지원 완료",
  SCREENING: "서류 검토",
  INTERVIEW: "면접 진행",
  ACCEPTED: "합격",
  REJECTED: "불합격",
};

export type CandidateJobPosition = string;

export type CandidateDocumentType =
  | "RESUME"
  | "PORTFOLIO"
  | "COVER_LETTER"
  | "CAREER_DESCRIPTION"
  | "ROLE_PROFILE";

export interface CandidateListRequest {
  page: number;
  limit: number;
  search?: string;
  applyStatus?: CandidateApplyStatus;
  /** 면접 세션의 target_job과 정확히 일치하는 지원자만 */
  targetJob?: string;
}

export interface ApplyStatusCountRow {
  applyStatus: string;
  count: number;
}

export interface TargetJobCountRow {
  targetJob: string;
  count: number;
}

export type DifficultyLevel = "JUNIOR" | "INTERMEDIATE" | "SENIOR";

export type AnalysisSessionStatus =
  | "DRAFT"
  | "READY"
  | "PROCESSING"
  | "COMPLETED"
  | "FAILED";

export interface PromptProfileOption {
  id: number;
  profileKey: string;
  targetJob: string | null;
  systemPromptPreview: string;
}

export type AnalysisSessionGraphPipeline = InterviewSessionGraphPipeline;

export interface AnalysisSessionCreateRequest {
  candidateIds: number[];
  targetJob: string;
  difficultyLevel?: DifficultyLevel | null;
  promptProfileId: number;
  promptProfileSnapshot?: Record<string, unknown> | null;
  graphPipeline: AnalysisSessionGraphPipeline;
}

export interface AnalysisSessionCreateItem {
  sessionId: number;
  candidateId: number;
  targetJob: string;
  difficultyLevel: DifficultyLevel | null;
  promptProfileId?: number | string | null;
  status: AnalysisSessionStatus;
  createdAt?: string;
}

export interface AnalysisSessionCreateResponse {
  items: AnalysisSessionCreateItem[];
}

export interface CandidateStatisticsResponse {
  totalCandidates: number;
  byApplyStatus: ApplyStatusCountRow[];
  byTargetJob: TargetJobCountRow[];
  activeWithoutInterviewSessionCount: number;
}

export interface CandidateCreateRequest {
  name: string;
  email: string;
  phone: string;
  jobPosition: CandidateJobPosition | null;
  birthDate: string | null;
}

export interface CandidateUpdateRequest {
  name: string;
  email: string;
  phone: string;
  jobPosition: CandidateJobPosition | null;
  birthDate: string | null;
}

export interface CandidateStatusPatchRequest {
  applyStatus: CandidateApplyStatus;
}

export interface CandidateDocumentResponse {
  id: number;
  documentType: CandidateDocumentType;
  title: string;
  originalFileName: string;
  storedFileName: string;
  filePath: string;
  fileExt: string | null;
  mimeType: string | null;
  fileSize: number | null;
  extractStatus: string;
  createdAt: string;
}

export interface CandidateDocumentDetailResponse
  extends CandidateDocumentResponse {
  extractedText: string | null;
}

export interface CandidateResponse {
  id: number;
  name: string;
  email: string;
  phone: string;
  birthDate: string | null;
  jobPosition: CandidateJobPosition | null;
  applyStatus: CandidateApplyStatus;
  createdAt: string;
  createdBy: number | null;
  createdName: string | null;
  updatedAt: string;
  deletedAt: string | null;
  deletedBy: number | null;
}

export interface CandidateDetailResponse extends CandidateResponse {
  documents: CandidateDocumentResponse[];
  screeningResult: ScreeningPreviewResult | null;
}

export type CandidateListResponse = PagedListResponse<CandidateResponse>;

export interface CandidateFormState {
  name: string;
  email: string;
  phone: string;
  jobPosition: CandidateJobPosition | "";
  birthDate: string;
  applyStatus: CandidateApplyStatus;
}

export type CandidateRegistrationMode = "single" | "documentBulk" | "sampleBulk";

export interface CandidatePendingDocument {
  id: string;
  file: File;
  documentType: CandidateDocumentType;
}

export interface CandidateDocumentUploadRequest {
  documentTypes: CandidateDocumentType[];
  files: File[];
}

export interface CandidateDocumentUploadResponse {
  candidateId: number;
  count: number;
  documents: CandidateDocumentResponse[];
}

export interface CandidateDocumentReplaceRequest {
  documentType: CandidateDocumentType;
  file: File;
}

export interface CandidateSampleFolder {
  folderName: string;
  candidateCount: number;
}

export interface CandidateBulkImportRequest {
  folderName: string;
}

export interface CandidateBulkImportError {
  candidateKey: string;
  reason: string;
}

export interface CandidateBulkImportResponse {
  folderName: string;
  requestedCount: number;
  createdCount: number;
  skippedCount: number;
  documentCount: number;
  errors: CandidateBulkImportError[];
}

export type DocumentBulkUploadMode = "ZIP" | "FILES";

export interface CandidateProfileExtractionOutput {
  name: string | null;
  email: string | null;
  phone: string | null;
  birthDate: string | null;
  jobPosition: string | null;
  summary: string | null;
  confidenceScore: number;
  missingFields: string[];
  warnings: string[];
}

export type ScreeningRecommendation =
  | "RECOMMEND"
  | "HOLD"
  | "NOT_RECOMMENDED"
  | "NEEDS_REVIEW"
  | string;

export type ScreeningDecisionStatus =
  | "PENDING"
  | "CONFIRMED"
  | "HELD"
  | "EXCLUDED"
  | string;

export interface ScreeningPreviewResult {
  recommendation: ScreeningRecommendation;
  score: number;
  confidence: number;
  summary: string | null;
  fitReasons: string[];
  riskFactors: string[];
  missingEvidence: string[];
  interviewFocus: string[];
  suggestedNextAction: string;
  scoreBreakdown: Record<string, unknown>;
  evidenceRefs: Record<string, unknown>[];
  warnings: string[];
  decisionStatus: ScreeningDecisionStatus | null;
}

export interface DocumentBulkImportPreviewDocument {
  originalFileName: string;
  storedFileName: string;
  filePath: string;
  fileExt: string | null;
  mimeType: string | null;
  fileSize: number | null;
  documentType: CandidateDocumentType;
  extractStatus: string;
  extractStrategy: string | null;
  extractQualityScore: number;
  extractSourceType: string | null;
  detectedDocumentType: string | null;
  extractedTextLength: number;
  extractedTextPreview: string | null;
  extractMeta: Record<string, unknown> | null;
  errorMessage: string | null;
}

export interface DocumentBulkImportPreviewRow {
  rowId: string;
  status: "READY" | "NEEDS_REVIEW" | "INVALID" | string;
  groupKey: string;
  inferredCandidateName: string | null;
  extractedProfile: CandidateProfileExtractionOutput;
  candidate: {
    name?: string | null;
    email?: string | null;
    phone?: string | null;
    birth_date?: string | null;
    job_position?: string | null;
    apply_status?: CandidateApplyStatus | string;
  };
  documents: DocumentBulkImportPreviewDocument[];
  documentCount: number;
  confidenceScore: number;
  duplicateCandidateId: number | null;
  errors: string[];
  warnings: string[];
  screeningPreview: ScreeningPreviewResult | null;
}

export interface DocumentBulkImportPreviewSummary {
  totalGroups: number;
  processedGroups: number;
  readyCount: number;
  needsReviewCount: number;
  invalidCount: number;
  documentCount: number;
}

export interface DocumentBulkImportPreviewResponse {
  jobId: number;
  uploadMode: DocumentBulkUploadMode;
  summary: DocumentBulkImportPreviewSummary;
  rows: DocumentBulkImportPreviewRow[];
}

export interface DocumentBulkImportPreviewStartResponse {
  jobId: number;
  status: string;
  progress: number;
  currentStep: string | null;
  message: string;
}

export interface DocumentBulkImportPreviewJobResponse {
  jobId: number;
  status: string;
  progress: number;
  currentStep: string | null;
  errorMessage: string | null;
  uploadMode: DocumentBulkUploadMode | null;
  summary: DocumentBulkImportPreviewSummary | null;
  rows: DocumentBulkImportPreviewRow[];
}

export interface DocumentBulkImportPreviewJobListResponse {
  jobs: DocumentBulkImportPreviewJobResponse[];
}

export interface DocumentBulkImportPreviewRequest {
  mode: DocumentBulkUploadMode;
  zipFile?: File | null;
  files?: File[];
  defaultJobPosition?: string;
  defaultApplyStatus?: CandidateApplyStatus;
}

export interface DocumentBulkImportConfirmRequest {
  jobId: number;
  selectedRowIds: string[];
}

export interface DocumentBulkImportConfirmError {
  rowId: string | null;
  groupKey: string | null;
  reason: string;
}

export interface DocumentBulkImportConfirmResponse {
  jobId: number;
  requestedCount: number;
  createdCount: number;
  skippedCount: number;
  documentCount: number;
  candidateIds: number[];
  errors: DocumentBulkImportConfirmError[];
}
