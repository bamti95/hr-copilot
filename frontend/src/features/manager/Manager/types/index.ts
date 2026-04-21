import type { PagedListResponse } from "../../../../common/types/pagination";

export interface ManagerListRequest {
  page: number;
  size: number;
  keyword?: string;
  status?: string;
  roleType?: string;
}

export interface ManagerCreateRequest {
  loginId: string;
  password: string;
  name: string;
  email: string;
  roleType: string;
  status: string;
}

export interface ManagerFormState {
  loginId: string;
  password: string;
  name: string;
  email: string;
  roleType: string;
  status: string;
}

export interface ManagerUpdateRequest {
  name: string;
  email: string;
  roleType: string;
  status: string;
  password?: string;
}

export interface ManagerStatusUpdateRequest {
  status: string;
}

export interface ManagerResponse {
  id: number;
  loginId: string;
  name: string;
  email: string;
  roleType: string | null;
  status: string;
  lastLoginAt: string | null;
  createdAt: string;
  createdBy: number | null;
  deletedAt: string | null;
  deletedBy: number | null;
}

export type ManagerListResponse = PagedListResponse<ManagerResponse>;
