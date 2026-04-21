import type { PagedListResponse } from "../../../../common/types/pagination";

export interface DocumentRequest {
  page: number;
  size: number;
  search?: string;
}

export interface DocumentResponse {
  id: number;
  title: string;
  documentType: string;
  candidateName: string;
  extractStatus: string;
  uploadedAt: string;
}

export type DocumentListResponse = PagedListResponse<DocumentResponse>;
