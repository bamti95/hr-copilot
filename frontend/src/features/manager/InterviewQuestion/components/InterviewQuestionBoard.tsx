import { DataTable } from "../../../../common/components/DataTable";
import { Pagination } from "../../../../common/components/Pagination";
import type {
  InterviewQuestionListResponse,
  InterviewQuestionResponse,
} from "../types";

interface InterviewQuestionBoardProps {
  data: InterviewQuestionListResponse;
  search: string;
  onSearchChange: (value: string) => void;
  onPageChange: (page: number) => void;
}

const searchInputClassName =
  "min-h-12 w-full rounded-full border border-[var(--line)] bg-[var(--panel-strong)] px-4 text-[var(--text)] outline-none transition focus:border-[var(--primary)] md:w-[320px]";

export function InterviewQuestionBoard({
  data,
  search,
  onSearchChange,
  onPageChange,
}: InterviewQuestionBoardProps) {
  return (
    <section className="rounded-[32px] border border-white/70 bg-[var(--panel)] p-7 shadow-[var(--shadow)] backdrop-blur-[14px]">
      <div className="mb-[18px] flex flex-col items-start justify-between gap-4">
        <div>
          <h2 className="m-0 text-2xl font-bold text-[var(--text)]">Interview Questions</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            질문, 기대 답변, 우선순위를 빠르게 검색할 수 있는 영역입니다.
          </p>
        </div>
        <input
          className={searchInputClassName}
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="question, category, rationale"
        />
      </div>
      <DataTable<InterviewQuestionResponse>
        columns={[
          { key: "category", header: "Category", render: (row) => row.category },
          { key: "questionText", header: "Question", render: (row) => row.questionText },
          { key: "expectedAnswer", header: "Expected Answer", render: (row) => row.expectedAnswer },
          { key: "priority", header: "Priority", render: (row) => row.priority },
        ]}
        rows={data.items}
        getRowKey={(row) => row.id}
      />
      <Pagination paging={data.paging} onPageChange={onPageChange} />
    </section>
  );
}
