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

export function InterviewQuestionBoard({
  data,
  search,
  onSearchChange,
  onPageChange,
}: InterviewQuestionBoardProps) {
  return (
    <section className="panel">
      <div className="panel__header panel__header--stack">
        <div>
          <h2>Interview Questions</h2>
          <p>질문, 기대 답변, 우선순위를 함께 검토하는 영역입니다.</p>
        </div>
        <input
          className="panel__search"
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
