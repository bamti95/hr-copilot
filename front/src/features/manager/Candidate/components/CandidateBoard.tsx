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

const searchInputClassName =
  "min-h-12 w-full rounded-full border border-[var(--line)] bg-[var(--panel-strong)] px-4 text-[var(--text)] outline-none transition focus:border-[var(--primary)] md:w-[320px]";

export function CandidateBoard({
  data,
  search,
  onSearchChange,
  onPageChange,
}: CandidateBoardProps) {
  return (
    <section className="rounded-[32px] border border-white/70 bg-[var(--panel)] p-7 shadow-[var(--shadow)] backdrop-blur-[14px]">
      <div className="mb-[18px] flex flex-col items-start justify-between gap-4">
        <div>
          <h2 className="m-0 text-2xl font-bold text-[var(--text)]">Candidate Pipeline</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            지원자 정보와 지원 상태를 하나의 파이프라인으로 확인합니다.
          </p>
        </div>
        <input
          className={searchInputClassName}
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
