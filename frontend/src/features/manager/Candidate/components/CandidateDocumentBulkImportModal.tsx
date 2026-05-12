import { useEffect, useState } from "react";
import { getJobPositionLabel } from "../../common/candidateJobPosition";
import {
  formatScreeningRecommendation,
  getDefaultScreeningSelectedRowIds,
  getScreeningPillClassName,
  getScreeningSummary,
} from "../utils/screening";
import { ScreeningPreviewDetails } from "./ScreeningPreviewDetails";
import type {
  CandidateApplyStatus,
  DocumentBulkImportPreviewRequest,
  DocumentBulkImportPreviewJobResponse,
  DocumentBulkUploadMode,
} from "../types";
import { CANDIDATE_APPLY_STATUS_LABEL } from "../types";

interface CandidateDocumentBulkImportModalProps {
  open: boolean;
  isSubmitting: boolean;
  isImporting: boolean;
  preview: DocumentBulkImportPreviewJobResponse | null;
  onClose: () => void;
  onPreview: (request: DocumentBulkImportPreviewRequest) => void;
  onConfirmImport: (selectedRowIds: string[]) => void;
}

const panelClassName =
  "max-h-[92vh] w-full max-w-6xl overflow-y-auto rounded-[28px] border border-white/70 bg-white p-6 shadow-2xl";

const inputClassName =
  "mt-2 h-11 w-full rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] px-4 text-[var(--text)] outline-none transition focus:border-[var(--primary)] disabled:cursor-not-allowed disabled:opacity-60";

const buttonClassName =
  "inline-flex h-11 items-center justify-center rounded-xl border px-4 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60";

const statusOptions: CandidateApplyStatus[] = [
  "APPLIED",
  "SCREENING",
  "INTERVIEW",
  "ACCEPTED",
  "REJECTED",
];

function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function formatFiles(files: File[]) {
  if (files.length === 0) {
    return "선택된 파일이 없습니다.";
  }
  if (files.length === 1) {
    return files[0].name;
  }
  return `${files.length} files selected`;
}

export function CandidateDocumentBulkImportModal({
  open,
  isSubmitting,
  isImporting,
  preview,
  onClose,
  onPreview,
  onConfirmImport,
}: CandidateDocumentBulkImportModalProps) {
  const [mode, setMode] = useState<DocumentBulkUploadMode>("ZIP");
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [defaultJobPosition, setDefaultJobPosition] = useState("");
  const [defaultApplyStatus, setDefaultApplyStatus] =
    useState<CandidateApplyStatus>("APPLIED");
  const [selectedRowIds, setSelectedRowIds] = useState<string[]>([]);

  const canSubmit =
    !isSubmitting && (mode === "ZIP" ? Boolean(zipFile) : files.length > 0);
  const summary = preview?.summary;
  const isJobRunning =
    preview?.status === "QUEUED" || preview?.status === "RUNNING" || preview?.status === "RETRYING";
  const importableRows = preview?.rows.filter((row) => row.status === "READY") ?? [];
  const selectedImportableRowIds = selectedRowIds.filter((rowId) =>
    importableRows.some((row) => row.rowId === rowId),
  );
  const screeningSummary = getScreeningSummary(preview?.rows ?? []);
  const canConfirmImport =
    Boolean(preview) &&
    !isJobRunning &&
    !isSubmitting &&
    !isImporting &&
    selectedImportableRowIds.length > 0;

  useEffect(() => {
    setSelectedRowIds(getDefaultScreeningSelectedRowIds(preview?.rows ?? []));
  }, [preview?.jobId, preview?.rows]);

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-4 backdrop-blur-sm">
      <div className={panelClassName}>
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <h3 className="text-xl font-bold text-[var(--text)]">
              문서 기반 지원자 일괄등록
            </h3>
            <p className="mt-2 text-sm text-[var(--muted)]">
              ZIP 또는 여러 문서를 업로드해 지원자별 미리보기를 생성합니다.
            </p>
          </div>
          <button
            type="button"
            className={`${buttonClassName} border-[var(--line)] text-[var(--muted)] hover:bg-slate-50`}
            onClick={onClose}
            disabled={isSubmitting}
          >
            닫기
          </button>
        </div>

        <div className="mt-5 grid gap-4 rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] p-4 lg:grid-cols-[220px_minmax(0,1fr)_220px_180px]">
          <label className="text-sm font-medium text-[var(--text)]">
            Upload mode
            <select
              className={inputClassName}
              value={mode}
              disabled={isSubmitting}
              onChange={(event) => setMode(event.target.value as DocumentBulkUploadMode)}
            >
              <option value="ZIP">압축파일</option>
              <option value="FILES">다중 파일 업로드</option>
            </select>
          </label>

          <label className="text-sm font-medium text-[var(--text)]">
            Files
            <input
              className={inputClassName}
              type="file"
              accept={mode === "ZIP" ? ".zip" : ".pdf,.doc,.docx,.txt,.hwp,.hwpx"}
              multiple={mode === "FILES"}
              disabled={isSubmitting}
              onChange={(event) => {
                const selected = Array.from(event.target.files ?? []);
                if (mode === "ZIP") {
                  setZipFile(selected[0] ?? null);
                } else {
                  setFiles(selected);
                }
              }}
            />
            <p className="mt-2 text-xs text-[var(--muted)]">
              {mode === "ZIP" ? zipFile?.name || "No ZIP selected" : formatFiles(files)}
            </p>
          </label>

          <label className="text-sm font-medium text-[var(--text)]">
            Default job
            <input
              className={inputClassName}
              value={defaultJobPosition}
              disabled={isSubmitting}
              onChange={(event) => setDefaultJobPosition(event.target.value)}
              placeholder="예: 백엔드 개발자"
            />
          </label>

          <label className="text-sm font-medium text-[var(--text)]">
            신청 상태
            <select
              className={inputClassName}
              value={defaultApplyStatus}
              disabled={isSubmitting}
              onChange={(event) =>
                setDefaultApplyStatus(event.target.value as CandidateApplyStatus)
              }
            >
              {statusOptions.map((status) => (
                <option key={status} value={status}>
                  {CANDIDATE_APPLY_STATUS_LABEL[status]}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="mt-5 flex justify-end gap-3">
          <button
            type="button"
            className={`${buttonClassName} border-[var(--line)] text-[var(--text)] hover:bg-slate-50`}
            onClick={onClose}
            disabled={isSubmitting}
          >
            취소
          </button>
          <button
            type="button"
            className={`${buttonClassName} border-transparent bg-[var(--primary)] text-white hover:opacity-90`}
            disabled={!canSubmit || isJobRunning}
            onClick={() =>
              onPreview({
                mode,
                zipFile,
                files,
                defaultJobPosition,
                defaultApplyStatus,
              })
            }
          >
            {isSubmitting ? "업로드중..." : isJobRunning ? "작업중..." : "미리보기 생성"}
          </button>
          <button
            type="button"
            className={`${buttonClassName} border-transparent bg-emerald-600 text-white hover:bg-emerald-700`}
            disabled={!canConfirmImport}
            onClick={() => onConfirmImport(selectedImportableRowIds)}
          >
            {isImporting
              ? "Importing..."
              : `READY ${selectedImportableRowIds.length}건 확정 등록`}
          </button>
        </div>

        {preview ? (
          <div className="mt-6">
            <div className="mb-4 rounded-2xl border border-[var(--line)] bg-white p-4">
              <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="text-xs font-semibold text-[var(--muted)]">작업 상태</p>
                  <p className="mt-1 text-sm font-bold text-[var(--text)]">
                    {preview.status}
                    {preview.currentStep ? ` / ${preview.currentStep}` : ""}
                  </p>
                </div>
                <p className="text-sm font-semibold text-[var(--text)]">
                  {preview.progress}%
                </p>
              </div>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-emerald-500 transition-all"
                  style={{ width: `${Math.max(0, Math.min(100, preview.progress))}%` }}
                />
              </div>
              {summary ? (
                <p className="mt-2 text-xs text-[var(--muted)]">
                  {summary.processedGroups} / {summary.totalGroups} groups processed
                </p>
              ) : null}
            </div>
            <div className="grid gap-3 md:grid-cols-6">
              <div className="rounded-2xl border border-[var(--line)] bg-white p-4">
                <p className="text-xs font-semibold text-[var(--muted)]">Job ID</p>
                <p className="mt-1 text-lg font-bold text-[var(--text)]">
                  {preview.jobId}
                </p>
              </div>
              <div className="rounded-2xl border border-[var(--line)] bg-white p-4">
                <p className="text-xs font-semibold text-[var(--muted)]">Groups</p>
                <p className="mt-1 text-lg font-bold text-[var(--text)]">
                  {summary?.totalGroups ?? 0}
                </p>
              </div>
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
                <p className="text-xs font-semibold text-emerald-700">Ready</p>
                <p className="mt-1 text-lg font-bold text-emerald-900">
                  {summary?.readyCount ?? 0}
                </p>
              </div>
              <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
                <p className="text-xs font-semibold text-amber-700">Review</p>
                <p className="mt-1 text-lg font-bold text-amber-900">
                  {summary?.needsReviewCount ?? 0}
                </p>
              </div>
              <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4">
                <p className="text-xs font-semibold text-rose-700">Invalid</p>
                <p className="mt-1 text-lg font-bold text-rose-900">
                  {summary?.invalidCount ?? 0}
                </p>
              </div>
              <div className="rounded-2xl border border-teal-200 bg-teal-50 p-4">
                <p className="text-xs font-semibold text-teal-700">Recommended</p>
                <p className="mt-1 text-lg font-bold text-teal-900">
                  {screeningSummary.recommended}
                </p>
              </div>
            </div>
            <div className="mt-3 rounded-2xl border border-[var(--line)] bg-white px-4 py-3 text-xs text-[var(--muted)]">
              Default import selects READY + Recommended rows. Hold or Not Recommended rows can be selected manually when they are READY.
            </div>

            <div className="mt-4 overflow-x-auto rounded-2xl border border-[var(--line)]">
              <table className="w-full border-collapse text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    {[
                      "Status",
                      "Select",
                      "Screening",
                      "Group",
                      "Name",
                      "Email",
                      "Phone",
                      "Birth",
                      "Job",
                      "Docs",
                      "Extraction",
                      "Confidence",
                      "Notes",
                    ].map((label) => (
                      <th
                        key={label}
                        className="border-b border-[var(--line)] px-3 py-3 text-left font-bold text-[var(--muted)]"
                      >
                        {label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.rows.map((row) => (
                    <tr key={row.rowId} className="align-top">
                      <td className="border-b border-[var(--line)] px-3 py-3 font-semibold">
                        {row.status}
                      </td>
                      <td className="border-b border-[var(--line)] px-3 py-3">
                        <input
                          type="checkbox"
                          className="h-4 w-4"
                          checked={selectedRowIds.includes(row.rowId)}
                          disabled={row.status !== "READY" || isImporting}
                          onChange={(event) => {
                            setSelectedRowIds((current) =>
                              event.target.checked
                                ? [...current, row.rowId]
                                : current.filter((rowId) => rowId !== row.rowId),
                            );
                          }}
                        />
                      </td>
                      <td className="border-b border-[var(--line)] px-3 py-3">
                        <div className="space-y-2">
                          <span
                            className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${getScreeningPillClassName(row.screeningPreview)}`}
                          >
                            {formatScreeningRecommendation(row.screeningPreview?.recommendation)}
                            {row.screeningPreview ? ` · ${row.screeningPreview.score}점` : ""}
                          </span>
                          {row.screeningPreview?.fitReasons[0] ? (
                            <p className="max-w-[220px] text-xs text-slate-600">
                              {row.screeningPreview.fitReasons[0]}
                            </p>
                          ) : null}
                          {row.screeningPreview?.riskFactors.length ? (
                            <p className="text-xs font-medium text-rose-600">
                              Risk {row.screeningPreview.riskFactors.length}
                            </p>
                          ) : null}
                          <ScreeningPreviewDetails screening={row.screeningPreview} />
                        </div>
                      </td>
                      <td className="border-b border-[var(--line)] px-3 py-3">
                        {row.groupKey}
                      </td>
                      <td className="border-b border-[var(--line)] px-3 py-3">
                        {row.candidate.name || "-"}
                      </td>
                      <td className="border-b border-[var(--line)] px-3 py-3">
                        {row.candidate.email || "-"}
                      </td>
                      <td className="border-b border-[var(--line)] px-3 py-3">
                        {row.candidate.phone || "-"}
                      </td>
                      <td className="border-b border-[var(--line)] px-3 py-3">
                        {row.candidate.birth_date || "-"}
                      </td>
                      <td className="border-b border-[var(--line)] px-3 py-3">
                        {row.candidate.job_position
                          ? getJobPositionLabel(row.candidate.job_position)
                          : "-"}
                      </td>
                      <td className="border-b border-[var(--line)] px-3 py-3">
                        {row.documentCount}
                      </td>
                      <td className="max-w-sm border-b border-[var(--line)] px-3 py-3">
                        <div className="space-y-2">
                          {row.documents.map((document) => (
                            <details key={document.storedFileName} className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
                              <summary className="cursor-pointer text-xs font-semibold text-slate-700">
                                {document.originalFileName} · {document.extractStatus} · {formatPercent(document.extractQualityScore)}
                              </summary>
                              <div className="mt-2 space-y-1 text-xs text-slate-600">
                                <p>type: {document.documentType}</p>
                                <p>strategy: {document.extractStrategy ?? "-"}</p>
                                <p>source: {document.extractSourceType ?? "-"}</p>
                                <p>detected: {document.detectedDocumentType ?? "-"}</p>
                                <p>text: {document.extractedTextLength.toLocaleString()}자</p>
                                {document.errorMessage ? <p>error: {document.errorMessage}</p> : null}
                                {document.extractedTextPreview ? (
                                  <p className="line-clamp-3">preview: {document.extractedTextPreview}</p>
                                ) : null}
                              </div>
                            </details>
                          ))}
                        </div>
                      </td>
                      <td className="border-b border-[var(--line)] px-3 py-3">
                        {formatPercent(row.confidenceScore)}
                      </td>
                      <td className="max-w-xs border-b border-[var(--line)] px-3 py-3">
                        {[...row.errors, ...row.warnings].join(" / ") || "-"}
                      </td>
                    </tr>
                  ))}
                  {preview.rows.length === 0 ? (
                    <tr>
                      <td
                        colSpan={13}
                        className="px-3 py-8 text-center text-[var(--muted)]"
                      >
                        No preview rows.
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
