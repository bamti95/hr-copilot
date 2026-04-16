import { opsLogList } from "../../../../common/data/managerConsoleData";
import { paginateItems } from "../../../../common/utils/paginate";
import type { OpsLogListResponse, OpsLogRequest, OpsLogResponse } from "../types";

export function fetchOpsLogList(request: OpsLogRequest): OpsLogListResponse {
  return paginateItems(opsLogList, request);
}

export function fetchOpsLogDetail(id: number): OpsLogResponse | undefined {
  return opsLogList.find((log) => log.id === id);
}
