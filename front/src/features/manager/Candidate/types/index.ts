import type { PagedListResponse } from "../../../../common/types/pagination";

export interface CandidateRequest {
  page: number;
  size: number;
  search?: string;
}

export interface CandidateResponse {
  id: number;
  name: string;
  email: string;
  phone: string;
  applyStatus: string;
  targetJob: string;
}

export type CandidateListResponse = PagedListResponse<CandidateResponse>;
