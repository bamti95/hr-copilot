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

function priorityTone(priority: string) {
  if (priority === "P1") {
    return "bg-rose-100 text-rose-700";
  }
  if (priority === "P2") {
    return "bg-amber-100 text-amber-800";
  }
  return "bg-slate-100 text-slate-700";
}

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
            질문 내용과 기대 답변을 더 읽기 쉽게 정리한 뷰입니다.
          </p>
        </div>

        <div className="flex w-full flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-wrap gap-2">
            <span className="inline-flex rounded-full border border-[var(--line)] bg-[var(--panel-strong)] px-3 py-1.5 text-xs font-semibold text-[var(--muted)]">
              Total {data.paging.totalCount}
            </span>
            <span className="inline-flex rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700">
              Session-linked mock view
            </span>
          </div>

          <input
            className={searchInputClassName}
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="question, category, rationale"
          />
        </div>
      </div>

      <DataTable<InterviewQuestionResponse>
        columns={[
          {
            key: "category",
            header: "Category",
            render: (row) => (
              <span className="inline-flex rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                {row.category}
              </span>
            ),
          },
          {
            key: "questionText",
            header: "Question",
            render: (row) => (
              <div className="max-w-[480px] whitespace-normal">
                <div className="font-semibold leading-6 text-[var(--text)]">
                  {row.questionText}
                </div>
              </div>
            ),
          },
          {
            key: "expectedAnswer",
            header: "Expected Answer",
            render: (row) => (
              <div className="max-w-[360px] whitespace-normal text-sm leading-6 text-[var(--muted)]">
                {row.expectedAnswer}
              </div>
            ),
          },
          {
            key: "priority",
            header: "Priority",
            render: (row) => (
              <span
                className={`inline-flex rounded-full px-3 py-1 text-xs font-bold ${priorityTone(row.priority)}`}
              >
                {row.priority}
              </span>
            ),
          },
        ]}
        rows={data.items}
        getRowKey={(row) => row.id}
      />

      <Pagination paging={data.paging} onPageChange={onPageChange} />
    </section>
  );
}
