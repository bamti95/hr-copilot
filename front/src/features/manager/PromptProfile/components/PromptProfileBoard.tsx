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

export function PromptProfileBoard({
  data,
  search,
  onSearchChange,
  onPageChange,
}: PromptProfileBoardProps) {
  return (
    <section className="panel">
      <div className="panel__header panel__header--stack">
        <div>
          <h2>Prompt Profiles</h2>
          <p>Persona와 output schema를 프로파일 단위로 관리합니다.</p>
        </div>
        <input
          className="panel__search"
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
