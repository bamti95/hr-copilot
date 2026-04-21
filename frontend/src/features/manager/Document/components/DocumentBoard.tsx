import { DataTable } from "../../../../common/components/DataTable";
import { Pagination } from "../../../../common/components/Pagination";
import { StatusPill } from "../../../../common/components/StatusPill";
import type { DocumentListResponse, DocumentResponse } from "../types";

interface DocumentBoardProps {
  data: DocumentListResponse;
  search: string;
  onSearchChange: (value: string) => void;
  onPageChange: (page: number) => void;
}

const searchInputClassName =
  "min-h-12 w-full rounded-full border border-[var(--line)] bg-[var(--panel-strong)] px-4 text-[var(--text)] outline-none transition focus:border-[var(--primary)] md:w-[320px]";

export function DocumentBoard({
  data,
  search,
  onSearchChange,
  onPageChange,
}: DocumentBoardProps) {
  return (
    <section className="rounded-[32px] border border-white/70 bg-[var(--panel)] p-7 shadow-[var(--shadow)] backdrop-blur-[14px]">
      <div className="mb-[18px] flex flex-col items-start justify-between gap-4">
        <div>
          <h2 className="m-0 text-2xl font-bold text-[var(--text)]">Document Mapping</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            지원자 업로드 문서와 OCR 상태를 한눈에 확인합니다.
          </p>
        </div>
        <input
          className={searchInputClassName}
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="document title, type, candidate"
        />
      </div>
      <DataTable<DocumentResponse>
        columns={[
          { key: "title", header: "Document", render: (row) => row.title },
          { key: "documentType", header: "Type", render: (row) => row.documentType },
          { key: "candidateName", header: "Candidate", render: (row) => row.candidateName },
          { key: "uploadedAt", header: "Uploaded", render: (row) => row.uploadedAt },
          { key: "extractStatus", header: "Extract", render: (row) => <StatusPill status={row.extractStatus} /> },
        ]}
        rows={data.items}
        getRowKey={(row) => row.id}
      />
      <Pagination paging={data.paging} onPageChange={onPageChange} />
    </section>
  );
}
