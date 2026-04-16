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

export function DocumentBoard({
  data,
  search,
  onSearchChange,
  onPageChange,
}: DocumentBoardProps) {
  return (
    <section className="panel">
      <div className="panel__header panel__header--stack">
        <div>
          <h2>Document Mapping</h2>
          <p>지원자와 업로드 문서, OCR 상태를 한눈에 묶습니다.</p>
        </div>
        <input
          className="panel__search"
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
