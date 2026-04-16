import { DataTable } from "../../../../common/components/DataTable";
import { Pagination } from "../../../../common/components/Pagination";
import { StatusPill } from "../../../../common/components/StatusPill";
import type { ManagerListResponse, ManagerResponse } from "../types";

interface ManagerBoardProps {
  data: ManagerListResponse;
  search: string;
  onSearchChange: (value: string) => void;
  onPageChange: (page: number) => void;
}

export function ManagerBoard({
  data,
  search,
  onSearchChange,
  onPageChange,
}: ManagerBoardProps) {
  return (
    <section className="panel">
      <div className="panel__header panel__header--stack">
        <div>
          <h2>Manager Directory</h2>
          <p>통합 계정과 권한 상태를 관리자 기준으로 정리합니다.</p>
        </div>
        <input
          className="panel__search"
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="manager, role, email"
        />
      </div>
      <DataTable<ManagerResponse>
        columns={[
          { key: "name", header: "Name", render: (row) => row.name },
          { key: "loginId", header: "Login ID", render: (row) => row.loginId },
          { key: "roleType", header: "Role", render: (row) => row.roleType },
          { key: "email", header: "Email", render: (row) => row.email },
          { key: "lastLoginAt", header: "Last Login", render: (row) => row.lastLoginAt },
          { key: "status", header: "Status", render: (row) => <StatusPill status={row.status} /> },
        ]}
        rows={data.items}
        getRowKey={(row) => row.id}
      />
      <Pagination paging={data.paging} onPageChange={onPageChange} />
    </section>
  );
}
