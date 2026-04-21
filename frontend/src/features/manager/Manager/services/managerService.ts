import api from "../../../../services/api";
import type { PagingMeta } from "../../../../common/types/pagination";
import type {
  ManagerCreateRequest,
  ManagerListRequest,
  ManagerListResponse,
  ManagerResponse,
  ManagerStatusUpdateRequest,
  ManagerUpdateRequest,
} from "../types";

interface ManagerListApiResponse {
  items: ManagerResponse[];
  totalCount: number;
  totalPages: number;
}

function toPagingMeta(request: ManagerListRequest, response: ManagerListApiResponse): PagingMeta {
  return {
    page: request.page + 1,
    size: request.size,
    totalCount: response.totalCount,
    totalPages: response.totalPages,
  };
}

export async function fetchManagerList(request: ManagerListRequest): Promise<ManagerListResponse> {
  const response = await api.get<ManagerListApiResponse>("/managers", {
    params: {
      page: request.page,
      size: request.size,
      keyword: request.keyword || undefined,
      status: request.status || undefined,
      roleType: request.roleType || undefined,
    },
  });

  return {
    items: response.data.items,
    paging: toPagingMeta(request, response.data),
  };
}

export async function fetchManagerDetail(id: number) {
  const response = await api.get<ManagerResponse>(`/managers/${id}`);
  return response.data;
}

export async function createManager(requestBody: ManagerCreateRequest) {
  const response = await api.post<ManagerResponse>("/managers", requestBody);
  return response.data;
}

export async function updateManager(managerId: number, requestBody: ManagerUpdateRequest) {
  const response = await api.put<ManagerResponse>(`/managers/${managerId}`, requestBody);
  return response.data;
}

export async function updateManagerStatus(
  managerId: number,
  requestBody: ManagerStatusUpdateRequest,
) {
  const response = await api.patch<ManagerResponse>(`/managers/${managerId}/status`, requestBody);
  return response.data;
}

export async function deleteManager(managerId: number) {
  await api.delete(`/managers/${managerId}`);
}
