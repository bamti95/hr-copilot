import api from "./api";
import type {
  AdminMenu,
  AdminMenuListResponse,
  AdminMenuRequest,
  AdminMenuTreeResponse,
} from "../types/admin";

export interface FetchAdminMenuListParams {
  page?: number;
  size?: number;
  keyword?: string;
  useTf?: "Y" | "N";
  parentId?: number;
}

export async function fetchAdminMenuList(params: FetchAdminMenuListParams = {}) {
  const response = await api.get<AdminMenuListResponse>("/admin-menus", {
    params,
  });

  return response.data;
}

export async function fetchAdminMenuDetail(menuId: number) {
  const response = await api.get<AdminMenu>(`/admin-menus/${menuId}`);
  return response.data;
}

export async function fetchAdminMenuTree(useTf?: "Y" | "N") {
  const response = await api.get<AdminMenuTreeResponse[]>("/admin-menus/tree", {
    params: { useTf },
  });

  return response.data;
}

export async function createAdminMenu(requestBody: AdminMenuRequest) {
  const response = await api.post<AdminMenu>("/admin-menus", requestBody);
  return response.data;
}

export async function updateAdminMenu(menuId: number, requestBody: AdminMenuRequest) {
  const response = await api.put<AdminMenu>(`/admin-menus/${menuId}`, requestBody);
  return response.data;
}

export async function deleteAdminMenu(menuId: number) {
  await api.delete(`/admin-menus/${menuId}`);
}
