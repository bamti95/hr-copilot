import { DataTable } from "../../../../common/components/DataTable";
import { Pagination } from "../../../../common/components/Pagination";
import { StatusPill } from "../../../../common/components/StatusPill";
import type {
  PromptProfileListResponse,
  PromptProfileResponse,
} from "../types";

interface PromptProfileBoardProps {
  data: PromptProfileListResponse;
  search: string;
  onSearchChange: (value: string) => void;
  onPageChange: (page: number) => void;
}

const searchInputClassName =
  "min-h-12 w-full rounded-full border border-[var(--line)] bg-[var(--panel-strong)] px-4 text-[var(--text)] outline-none transition focus:border-[var(--primary)] md:w-[320px]";

export function PromptProfileBoard({
  data,
  search,
  onSearchChange,
  onPageChange,
}: PromptProfileBoardProps) {
  return (
    <section className="rounded-[32px] border border-white/70 bg-[var(--panel)] p-7 shadow-[var(--shadow)] backdrop-blur-[14px]">
      <div className="mb-[18px] flex flex-col items-start justify-between gap-4">
        <div>
          <h2 className="m-0 text-2xl font-bold text-[var(--text)]">Prompt Profiles</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Persona와 output schema를 프로파일 단위로 관리합니다.
          </p>
        </div>
        <input
          className={searchInputClassName}
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="profile key, persona"
        />
      </div>
      <DataTable<PromptProfileResponse>
        columns={[
          { key: "profileKey", header: "Profile Key", render: (row) => row.profileKey },
          { key: "persona", header: "Persona", render: (row) => row.persona },
          { key: "outputSchema", header: "Output Schema", render: (row) => row.outputSchema },
          { key: "status", header: "Status", render: (row) => <StatusPill status={row.status} /> },
        ]}
        rows={data.items}
        getRowKey={(row) => row.id}
      />
      <Pagination paging={data.paging} onPageChange={onPageChange} />
    </section>
  );
}
