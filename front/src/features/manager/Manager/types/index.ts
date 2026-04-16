import type { PagedListResponse } from "../../../../common/types/pagination";

export interface ManagerRequest {
  page: number;
  size: number;
  search?: string;
}

export interface ManagerResponse {
  id: number;
  loginId: string;
  name: string;
  email: string;
  roleType: string;
  status: string;
  lastLoginAt: string;
}

export type ManagerListResponse = PagedListResponse<ManagerResponse>;
