import { useLayoutEffect, useRef } from "react";
import { Pagination } from "../../../../common/components/Pagination";
import { StatusPill } from "../../../../common/components/StatusPill";
import { getJobPositionLabel } from "../../common/candidateJobPosition";
import { formatDateTime } from "../../common/formatDateTime";

import type {
  CandidateApplyStatus,
  CandidateListResponse,
  CandidateResponse,
  CandidateStatisticsResponse,
  DocumentBulkImportPreviewJobResponse,
} from "../types";

interface CandidateBoardProps {
  data: CandidateListResponse;
  statistics: CandidateStatisticsResponse | null;
  isLoading: boolean;
  search: string;
  statusFilter: CandidateApplyStatus | "ALL";
  jobFilter: string;
  pageSize: number;
  selectedIds: number[];
  onSearchChange: (value: string) => void;
  onSearchSubmit: () => void;
  onStatusFilterChange: (value: CandidateApplyStatus | "ALL") => void;
  onJobFilterChange: (value: string) => void;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  onCreate: () => void;
  onOpenBulkImport: () => void;
  onOpenDocumentBulkImport: () => void;
  documentBulkPreview: DocumentBulkImportPreviewJobResponse | null;
  isDocumentBulkJobActive: boolean;
  onView: (candidateId: number) => void;
  onDelete: (row: CandidateResponse) => void;
  onToggleSelect: (candidateId: number) => void;
  onSelectAllOnPage: () => void;
  onOpenAnalysisSessionCreateModal: () => void;
}

const inputClassName =
  "mt-2 h-12 w-full rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] px-4 text-[var(--text)] outline-none transition focus:border-[var(--primary)]";

const buttonClassName =
  "inline-flex h-10 items-center justify-center rounded-xl border px-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50";

function formatDate(value: string | null) {
  return value ? value.slice(0, 10) : "-";
}



export function CandidateBoard({
  data,
  statistics,
  isLoading,
  search,
  statusFilter,
  jobFilter,
  pageSize,
  selectedIds,
  onSearchChange,
  onSearchSubmit,
  onStatusFilterChange,
  onJobFilterChange,
  onPageChange,
  onPageSizeChange,
  onCreate,
  onOpenBulkImport,
  onOpenDocumentBulkImport,
  documentBulkPreview,
  isDocumentBulkJobActive,
  onView,
  onDelete,
  onToggleSelect,
  onSelectAllOnPage,
  onOpenAnalysisSessionCreateModal,
}: CandidateBoardProps) {
  const idsOnPage = data.items.map((row) => row.id);
  const allOnPageSelected =
    idsOnPage.length > 0 && idsOnPage.every((id) => selectedIds.includes(id));
  const someOnPageSelected = idsOnPage.some((id) => selectedIds.includes(id));
  const jobSelected = Boolean(jobFilter.trim());
  const canCreateAnalysisSession =
    jobSelected && selectedIds.length > 0 && !isLoading;
  const documentBulkSummary = documentBulkPreview?.summary;

  const headerCheckboxRef = useRef<HTMLInputElement>(null);
  useLayoutEffect(() => {
    const element = headerCheckboxRef.current;
    if (element) {
      element.indeterminate = !allOnPageSelected && someOnPageSelected;
    }
  }, [allOnPageSelected, someOnPageSelected]);

  return (
    <section className="rounded-4xl border border-white/70 bg-(--panel) p-7 shadow-(--shadow) backdrop-blur-[14px]">
      <div className="mb-5">
        <h2 className="text-2xl font-bold text-(--text)">지원자 관리</h2>
        <p className="mt-2 text-sm text-(--muted)">
          지원자를 직무와 상태 기준으로 조회하고, 선택한 지원자를 기반으로 분석 세션까지
          준비할 수 있습니다.
        </p>
      </div>

      {documentBulkPreview ? (
        <button
          type="button"
          className={`mb-4 flex w-full flex-col gap-3 rounded-3xl border px-4 py-3 text-left transition md:flex-row md:items-center md:justify-between ${
            isDocumentBulkJobActive
              ? "border-emerald-200 bg-emerald-50 hover:bg-emerald-100"
              : documentBulkPreview.status === "FAILED"
                ? "border-rose-200 bg-rose-50 hover:bg-rose-100"
                : "border-slate-200 bg-white hover:bg-slate-50"
          }`}
          onClick={onOpenDocumentBulkImport}
        >
          <div>
            <p className="text-sm font-bold text-slate-900">
              문서 일괄등록 작업 #{documentBulkPreview.jobId} · {documentBulkPreview.status}
            </p>
            <p className="mt-1 text-xs text-slate-600">
              {documentBulkPreview.currentStep || "작업 상태를 확인하는 중입니다."}
              {documentBulkSummary
                ? ` · ${documentBulkSummary.processedGroups}/${documentBulkSummary.totalGroups} 그룹 처리`
                : ""}
            </p>
          </div>
          <div className="min-w-48">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
              <span>{documentBulkPreview.progress}%</span>
              <span>{documentBulkPreview.rows.length} rows</span>
            </div>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/70">
              <div
                className="h-full rounded-full bg-emerald-500 transition-all"
                style={{
                  width: `${Math.max(0, Math.min(100, documentBulkPreview.progress))}%`,
                }}
              />
            </div>
          </div>
        </button>
      ) : null}

      <div className="mb-4 grid gap-3 rounded-3xl border border-white/70 bg-(--panel-strong) p-4 xl:grid-cols-[minmax(0,1fr)_160px_160px_150px_100px_auto_auto_auto_auto] xl:items-end">
        <label className="text-sm font-medium text-(--text)">
          검색어
          <input
            className={inputClassName}
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                onSearchSubmit();
              }
            }}
            placeholder="이름 또는 이메일로 검색"
          />
        </label>

        <label className="text-sm font-medium text-(--text)">
          지원 직무
          <select
            className={inputClassName}
            value={jobFilter}
            onChange={(event) => onJobFilterChange(event.target.value)}
            disabled={isLoading}
          >
            <option value="">전체</option>
            {(statistics?.byTargetJob ?? []).map((row) => (
              <option key={row.targetJob} value={row.targetJob}>
                {getJobPositionLabel(row.targetJob)} ({row.count})
              </option>
            ))}
          </select>
        </label>

        <label className="text-sm font-medium text-[var(--text)]">
          지원 상태
          <select
            className={inputClassName}
            value={statusFilter}
            onChange={(event) =>
              onStatusFilterChange(event.target.value as CandidateApplyStatus | "ALL")
            }
          >
            <option value="ALL">전체</option>
            <option value="APPLIED">APPLIED</option>
            <option value="SCREENING">SCREENING</option>
            <option value="INTERVIEW">INTERVIEW</option>
            <option value="ACCEPTED">ACCEPTED</option>
            <option value="REJECTED">REJECTED</option>
          </select>
        </label>

        <label className="text-sm font-medium text-(--text)">
          페이지 크기
          <select
            className={inputClassName}
            value={pageSize}
            onChange={(event) => onPageSizeChange(Number(event.target.value))}
          >
            {[10, 20, 50, 100].map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          className={`${buttonClassName} border-slate-900 bg-slate-900 px-4 text-white hover:bg-slate-800`}
          onClick={onSearchSubmit}
        >
          검색
        </button>

        <button
          type="button"
          className={`${buttonClassName} border-transparent bg-(--primary) px-4 text-white hover:opacity-90`}
          onClick={onCreate}
        >
          신규 등록
        </button>

        <button
          type="button"
          className={`${buttonClassName} border-emerald-300 bg-emerald-50 px-4 text-emerald-800 hover:bg-emerald-100`}
          onClick={onOpenBulkImport}
        >
          단체 지원자 등록
        </button>

        <button
          type="button"
          className={`${buttonClassName} border-teal-300 bg-teal-50 px-4 text-teal-900 hover:bg-teal-100`}
          onClick={onOpenDocumentBulkImport}
        >
          문서 일괄등록
        </button>

        <button
          type="button"
          className={`${buttonClassName} border-violet-300 bg-violet-50 px-3 text-violet-900 hover:bg-violet-100`}
          onClick={onOpenAnalysisSessionCreateModal}
          disabled={!canCreateAnalysisSession}
          title={
            !jobSelected
              ? "직무를 먼저 선택해 주세요."
              : selectedIds.length === 0
                ? "지원자를 한 명 이상 선택해 주세요."
                : undefined
          }
        >
          분석 세션 생성
        </button>
      </div>

      <div className="mb-4 flex items-center justify-between gap-3 text-sm text-(--muted)">
        <span>
          총 {data.paging.totalCount}건 / {Math.max(data.paging.totalPages, 1)} 페이지
        </span>
        <span>선택한 지원자 {selectedIds.length}명</span>
      </div>

      <div className="overflow-x-auto rounded-3xl border border-white/70">
        <table className="w-full border-collapse">
          <thead className="bg-white/60">
            <tr>
              <th className="w-10 border-b border-(--line) px-2 py-3 text-left text-[0.84rem] font-bold whitespace-nowrap text-[var(--muted)]">
                <input
                  ref={headerCheckboxRef}
                  type="checkbox"
                  className="h-4 w-4 rounded border-(--line)"
                  checked={allOnPageSelected}
                  onChange={onSelectAllOnPage}
                  disabled={isLoading || data.items.length === 0}
                />
              </th>
              {["ID", "이름", "이메일", "전화번호", "생년월일", "지원 상태", "생성자", "등록일", "액션"].map(
                (label) => (
                  <th
                    key={label}
                    className="border-b border-[var(--line)] px-3 py-3 text-left text-[0.84rem] font-bold whitespace-nowrap text-[var(--muted)]"
                  >
                    {label}
                  </th>
                ),
              )}
            </tr>
          </thead>
          <tbody>
            {data.items.map((row) => (
              <tr key={row.id} className="transition hover:bg-slate-50/70">
                <td className="border-b border-[var(--line)] px-2 py-3 whitespace-nowrap">
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-[var(--line)]"
                    checked={selectedIds.includes(row.id)}
                    onChange={() => onToggleSelect(row.id)}
                    disabled={isLoading}
                  />
                </td>
                <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">
                  {row.id}
                </td>
                <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap font-semibold text-[var(--text)]">
                  {row.name}
                </td>
                <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">
                  {row.email}
                </td>
                <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">
                  {row.phone}
                </td>
                <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">
                  {formatDate(row.birthDate)}
                </td>
                <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">
                  <StatusPill status={row.applyStatus} />
                </td>
                <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">
                  {row.createdName ?? "-"}
                </td>
                <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">
                  {formatDateTime(row.createdAt)}
                </td>
                <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      className={`${buttonClassName} border-sky-200 bg-sky-50 text-sky-700 hover:bg-sky-100`}
                      onClick={() => onView(row.id)}
                      disabled={isLoading}
                    >
                      상세
                    </button>
                    <button
                      type="button"
                      className={`${buttonClassName} border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100`}
                      onClick={() => onDelete(row)}
                      disabled={isLoading}
                    >
                      삭제
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {data.items.length === 0 ? (
              <tr>
                <td
                  colSpan={10}
                  className="px-3 py-10 text-center text-sm text-[var(--muted)]"
                >
                  조회된 지원자가 없습니다.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      <Pagination paging={data.paging} onPageChange={onPageChange} />
    </section>
  );
}
