import { DataTable } from "../../../../common/components/DataTable";
import { Pagination } from "../../../../common/components/Pagination";
import { StatusPill } from "../../../../common/components/StatusPill";
import { formatNumber } from "../../../../common/utils/format";
import type { OpsLogListResponse, OpsLogResponse } from "../types";

interface OpsLogBoardProps {
  data: OpsLogListResponse;
  search: string;
  onSearchChange: (value: string) => void;
  onPageChange: (page: number) => void;
}

export function OpsLogBoard({
  data,
  search,
  onSearchChange,
  onPageChange,
}: OpsLogBoardProps) {
  return (
    <section className="panel">
      <div className="panel__header panel__header--stack">
        <div>
          <h2>LLM Ops Logs</h2>
          <p>모델명, 토큰, 비용, 호출 상태를 운영 기준으로 추적합니다.</p>
        </div>
        <input
          className="panel__search"
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="model, candidate, status"
        />
      </div>
      <DataTable<OpsLogResponse>
        columns={[
          { key: "modelName", header: "Model", render: (row) => row.modelName },
          { key: "candidateName", header: "Candidate", render: (row) => row.candidateName },
          { key: "totalTokens", header: "Tokens", render: (row) => formatNumber(row.totalTokens) },
          { key: "costAmount", header: "Cost", render: (row) => row.costAmount },
          { key: "callStatus", header: "Status", render: (row) => <StatusPill status={row.callStatus} /> },
        ]}
        rows={data.items}
        getRowKey={(row) => row.id}
      />
      <Pagination paging={data.paging} onPageChange={onPageChange} />
    </section>
  );
}
