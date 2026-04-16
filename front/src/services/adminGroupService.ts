import api from "./api";
import type {
  AdminGroupListResponse,
  AdminGroupRequest,
  AdminGroupResponse,
} from "../types/admin";

export interface FetchAdminGroupListParams {
  page?: number;
  size?: number;
  keyword?: string;
  useTf?: "Y" | "N";
}

export async function fetchAdminGroupList(
  params: FetchAdminGroupListParams = {},
) {
  const response = await api.get<AdminGroupListResponse>("/admin-groups", {
    params,
  });

  return response.data;
}

export async function fetchAdminGroupDetail(adminGroupId: number) {
  const response = await api.get<AdminGroupResponse>(`/admin-groups/${adminGroupId}`);
  return response.data;
}

export async function createAdminGroup(requestBody: AdminGroupRequest) {
  const response = await api.post<AdminGroupResponse>("/admin-groups", requestBody);
  return response.data;
}

export async function updateAdminGroup(
  adminGroupId: number,
  requestBody: AdminGroupRequest,
) {
  const response = await api.put<AdminGroupResponse>(
    `/admin-groups/${adminGroupId}`,
    requestBody,
  );
  return response.data;
}

export async function deleteAdminGroup(adminGroupId: number) {
  await api.delete(`/admin-groups/${adminGroupId}`);
}
