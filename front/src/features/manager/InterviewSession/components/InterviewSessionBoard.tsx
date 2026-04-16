import { DataTable } from "../../../../common/components/DataTable";
import { Pagination } from "../../../../common/components/Pagination";
import { StatusPill } from "../../../../common/components/StatusPill";
import type {
  InterviewSessionListResponse,
  InterviewSessionResponse,
} from "../types";

interface InterviewSessionBoardProps {
  data: InterviewSessionListResponse;
  search: string;
  onSearchChange: (value: string) => void;
  onPageChange: (page: number) => void;
}

export function InterviewSessionBoard({
  data,
  search,
  onSearchChange,
  onPageChange,
}: InterviewSessionBoardProps) {
  return (
    <section className="panel">
      <div className="panel__header panel__header--stack">
        <div>
          <h2>Interview Sessions</h2>
          <p>후보자와 JD를 조합한 인터뷰 세션 생성 현황입니다.</p>
        </div>
        <input
          className="panel__search"
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="candidate, job, difficulty"
        />
      </div>
      <DataTable<InterviewSessionResponse>
        columns={[
          { key: "candidateName", header: "Candidate", render: (row) => row.candidateName },
          { key: "targetJob", header: "Target Job", render: (row) => row.targetJob },
          { key: "difficultyLevel", header: "Difficulty", render: (row) => row.difficultyLevel },
          { key: "questionCount", header: "Questions", render: (row) => row.questionCount },
          { key: "status", header: "Status", render: (row) => <StatusPill status={row.status} /> },
        ]}
        rows={data.items}
        getRowKey={(row) => row.id}
      />
      <Pagination paging={data.paging} onPageChange={onPageChange} />
    </section>
  );
}
