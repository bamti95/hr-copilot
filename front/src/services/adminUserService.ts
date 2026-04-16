import api from "./api";
import type { AdminListResponse, AdminRequest, AdminResponse } from "../types/admin";

export interface FetchAdminListParams {
  page?: number;
  size?: number;
  keyword?: string;
  status?: string;
  useTf?: "Y" | "N";
}

export async function fetchAdminList(params: FetchAdminListParams = {}) {
  const response = await api.get<AdminListResponse>("/admins", {
    params,
  });

  return response.data;
}

export async function fetchAdminDetail(adminId: number) {
  const response = await api.get<AdminResponse>(`/admins/${adminId}`);
  return response.data;
}

export async function createAdmin(requestBody: AdminRequest) {
  const response = await api.post<AdminResponse>("/admins", requestBody);
  return response.data;
}

export async function updateAdmin(adminId: number, requestBody: AdminRequest) {
  const response = await api.put<AdminResponse>(`/admins/${adminId}`, requestBody);
  return response.data;
}

export async function deleteAdmin(adminId: number) {
  await api.delete(`/admins/${adminId}`);
}
