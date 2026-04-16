import type { PagedListResponse } from "../../../../common/types/pagination";

export interface OpsLogRequest {
  page: number;
  size: number;
  search?: string;
}

export interface OpsLogResponse {
  id: number;
  modelName: string;
  candidateName: string;
  totalTokens: number;
  costAmount: string;
  callStatus: string;
}

export type OpsLogListResponse = PagedListResponse<OpsLogResponse>;
