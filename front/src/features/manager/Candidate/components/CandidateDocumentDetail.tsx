import { ArrowLeft, Download, FileText } from "lucide-react";
import { StatusPill } from "../../../../common/components/StatusPill";
import type {
  CandidateDetailResponse,
  CandidateDocumentDetailResponse,
} from "../types";

interface CandidateDocumentDetailProps {
  candidate: CandidateDetailResponse | null;
  document: CandidateDocumentDetailResponse | null;
  isLoading: boolean;
  onBack: () => void;
  onDownload: () => void;
}

function formatDateTime(value?: string) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  const hh = String(date.getHours()).padStart(2, "0");
  const min = String(date.getMinutes()).padStart(2, "0");

  return `${yyyy}-${mm}-${dd} ${hh}:${min}`;
}

function formatFileSize(value: number | null) {
  if (!value) {
    return "-";
  }

  if (value < 1024) {
    return `${value} B`;
  }

  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }

  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function getExtractMessage(document: CandidateDocumentDetailResponse | null) {
  if (!document) {
    return "문서 정보를 불러오는 중입니다.";
  }

  if (document.extractStatus === "PENDING") {
    return "텍스트 추출이 아직 진행 중입니다.";
  }

  if (document.extractStatus === "FAILED") {
    return "텍스트 추출에 실패했거나 추출 가능한 본문이 없습니다.";
  }

  return "추출된 텍스트가 없습니다.";
}

export function CandidateDocumentDetail({
  candidate,
  document,
  isLoading,
  onBack,
  onDownload,
}: CandidateDocumentDetailProps) {
  return (
    <section className="rounded-[32px] border border-white/70 bg-[var(--panel)] p-7 shadow-[var(--shadow)] backdrop-blur-[14px]">
      <div className="flex flex-col gap-4 border-b border-[var(--line)] pb-5 md:flex-row md:items-start md:justify-between">
        <div className="flex items-start gap-4">
          <button
            type="button"
            className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-slate-200 bg-white text-slate-500 transition hover:bg-slate-50 hover:text-slate-700"
            onClick={onBack}
            aria-label="지원자 상세로 이동"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>

          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-600">
              Document
            </p>
            <h2 className="mt-2 text-2xl font-bold text-[var(--text)]">
              {document?.originalFileName ?? "문서 상세"}
            </h2>
            <p className="mt-2 text-sm text-[var(--muted)]">
              {candidate ? `${candidate.name} 지원자의 문서 상세와 추출 텍스트를 확인합니다.` : "문서 메타 정보와 추출 결과를 확인합니다."}
            </p>
          </div>
        </div>

        {document ? <StatusPill status={document.extractStatus} /> : null}
      </div>

      {isLoading ? (
        <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-10 text-center text-sm text-[var(--muted)]">
          문서 상세 정보를 불러오는 중입니다.
        </div>
      ) : (
        <div className="mt-6 grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
          <aside className="space-y-4">
            <div className="rounded-[28px] border border-white/70 bg-[var(--panel-strong)] p-5">
              <h3 className="text-lg font-bold text-[var(--text)]">문서 정보</h3>

              <div className="mt-4 space-y-3 text-sm text-slate-600">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
                    Candidate
                  </p>
                  <p className="mt-1 text-sm font-semibold text-slate-900">
                    {candidate?.name ?? "-"}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
                    Document Type
                  </p>
                  <p className="mt-1 text-sm font-semibold text-slate-900">
                    {document?.documentType ?? "-"}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
                    File Size
                  </p>
                  <p className="mt-1 text-sm font-semibold text-slate-900">
                    {formatFileSize(document?.fileSize ?? null)}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
                    Created At
                  </p>
                  <p className="mt-1 text-sm font-semibold text-slate-900">
                    {formatDateTime(document?.createdAt)}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
                    Extract Status
                  </p>
                  <p className="mt-1 text-sm font-semibold text-slate-900">
                    {document?.extractStatus ?? "-"}
                  </p>
                </div>
              </div>

              <button
                type="button"
                className="mt-5 inline-flex h-11 w-full items-center justify-center gap-2 rounded-2xl border border-sky-200 bg-sky-50 px-4 text-sm font-semibold text-sky-700 transition hover:bg-sky-100"
                onClick={onDownload}
                disabled={!document}
              >
                <Download className="h-4 w-4" />
                문서 다운로드
              </button>
            </div>
          </aside>

          <div className="rounded-[28px] border border-white/70 bg-[var(--panel-strong)] p-5">
            <div className="flex items-center gap-3">
              <FileText className="h-5 w-5 text-emerald-600" />
              <div>
                <h3 className="text-lg font-bold text-[var(--text)]">추출 텍스트</h3>
                <p className="mt-1 text-sm text-[var(--muted)]">
                  OCR 및 텍스트 추출 결과를 확인하는 영역입니다.
                </p>
              </div>
            </div>

            {document?.extractedText ? (
              <div className="mt-5 rounded-2xl border border-slate-200 bg-white p-5">
                <pre className="max-h-[70vh] overflow-auto whitespace-pre-wrap break-words text-sm leading-7 text-slate-700">
                  {document.extractedText}
                </pre>
              </div>
            ) : (
              <div className="mt-5 rounded-2xl border border-dashed border-slate-300 bg-white px-5 py-12 text-center text-sm text-[var(--muted)]">
                {getExtractMessage(document)}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
