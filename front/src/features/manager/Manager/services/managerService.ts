import { managerList } from "../../../../common/data/managerConsoleData";
import { paginateItems } from "../../../../common/utils/paginate";
import type { ManagerListResponse, ManagerRequest, ManagerResponse } from "../types";

export function fetchManagerList(request: ManagerRequest): ManagerListResponse {
  return paginateItems(managerList, request);
}

export function fetchManagerDetail(id: number): ManagerResponse | undefined {
  return managerList.find((manager) => manager.id === id);
}
