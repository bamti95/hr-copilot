import type { PagedListResponse } from "../../../../common/types/pagination";

export type CandidateApplyStatus =
  | "APPLIED"
  | "SCREENING"
  | "INTERVIEW"
  | "ACCEPTED"
  | "REJECTED";

export type CandidateJobPosition =
  | "STRATEGY_PLANNING"
  | "HR"
  | "MARKETING"
  | "AI_DEV_DATA"
  | "SALES";

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

export interface AnalysisSessionCreateRequest {
  candidateIds: number[];
  targetJob: string;
  difficultyLevel?: DifficultyLevel | null;
  promptProfileId: number;
  promptProfileSnapshot?: Record<string, unknown> | null;
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
  updatedAt: string;
  deletedAt: string | null;
  deletedBy: number | null;
}

export interface CandidateDetailResponse extends CandidateResponse {
  documents: CandidateDocumentResponse[];
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
