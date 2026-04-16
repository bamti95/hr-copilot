import { DataTable } from "../../../../common/components/DataTable";
import { Pagination } from "../../../../common/components/Pagination";
import { StatusPill } from "../../../../common/components/StatusPill";
import type { CandidateListResponse, CandidateResponse } from "../types";

interface CandidateBoardProps {
  data: CandidateListResponse;
  search: string;
  onSearchChange: (value: string) => void;
  onPageChange: (page: number) => void;
}

export function CandidateBoard({
  data,
  search,
  onSearchChange,
  onPageChange,
}: CandidateBoardProps) {
  return (
    <section className="panel">
      <div className="panel__header panel__header--stack">
        <div>
          <h2>Candidate Pipeline</h2>
          <p>지원자 정보와 지원 상태를 하나의 파이프라인으로 확인합니다.</p>
        </div>
        <input
          className="panel__search"
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="candidate, status, target job"
        />
      </div>
      <DataTable<CandidateResponse>
        columns={[
          { key: "name", header: "Candidate", render: (row) => row.name },
          { key: "targetJob", header: "Target Job", render: (row) => row.targetJob },
          { key: "email", header: "Email", render: (row) => row.email },
          { key: "phone", header: "Phone", render: (row) => row.phone },
          { key: "applyStatus", header: "Status", render: (row) => <StatusPill status={row.applyStatus} /> },
        ]}
        rows={data.items}
        getRowKey={(row) => row.id}
      />
      <Pagination paging={data.paging} onPageChange={onPageChange} />
    </section>
  );
}
