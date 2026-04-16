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

const searchInputClassName =
  "min-h-12 w-full rounded-full border border-[var(--line)] bg-[var(--panel-strong)] px-4 text-[var(--text)] outline-none transition focus:border-[var(--primary)] md:w-[320px]";

export function InterviewSessionBoard({
  data,
  search,
  onSearchChange,
  onPageChange,
}: InterviewSessionBoardProps) {
  return (
    <section className="rounded-[32px] border border-white/70 bg-[var(--panel)] p-7 shadow-[var(--shadow)] backdrop-blur-[14px]">
      <div className="mb-[18px] flex flex-col items-start justify-between gap-4">
        <div>
          <h2 className="m-0 text-2xl font-bold text-[var(--text)]">Interview Sessions</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            후보자와 JD를 조합한 인터뷰 세션 생성 현황입니다.
          </p>
        </div>
        <input
          className={searchInputClassName}
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
