import type { PagedListResponse } from "../../../../common/types/pagination";

export type CandidateApplyStatus =
  | "APPLIED"
  | "SCREENING"
  | "INTERVIEW"
  | "ACCEPTED"
  | "REJECTED";

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
}

export interface CandidateCreateRequest {
  name: string;
  email: string;
  phone: string;
  birthDate: string | null;
}

export interface CandidateUpdateRequest {
  name: string;
  email: string;
  phone: string;
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

export interface CandidateResponse {
  id: number;
  name: string;
  email: string;
  phone: string;
  birthDate: string | null;
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
