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

const searchInputClassName =
  "min-h-12 w-full rounded-full border border-[var(--line)] bg-[var(--panel-strong)] px-4 text-[var(--text)] outline-none transition focus:border-[var(--primary)] md:w-[320px]";

export function OpsLogBoard({
  data,
  search,
  onSearchChange,
  onPageChange,
}: OpsLogBoardProps) {
  return (
    <section className="rounded-[32px] border border-white/70 bg-[var(--panel)] p-7 shadow-[var(--shadow)] backdrop-blur-[14px]">
      <div className="mb-[18px] flex flex-col items-start justify-between gap-4">
        <div>
          <h2 className="m-0 text-2xl font-bold text-[var(--text)]">LLM Ops Logs</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            모델명, 토큰, 비용, 호출 상태를 운영 기준으로 추적합니다.
          </p>
        </div>
        <input
          className={searchInputClassName}
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
