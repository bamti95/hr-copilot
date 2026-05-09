import { useState } from "react";
import {
  ArrowLeft,
  Download,
  FileText,
  LoaderCircle,
  Paperclip,
  RefreshCcw,
  Trash2,
  Upload,
} from "lucide-react";
import { StatusPill } from "../../../../common/components/StatusPill";
import { getJobPositionLabel } from "../../common/candidateJobPosition";
import { CANDIDATE_APPLY_STATUS_LABEL } from "../types";
import type {
  CandidateApplyStatus,
  CandidateDetailResponse,
  CandidateDocumentResponse,
  CandidateDocumentType,
  CandidateFormState,
  CandidateJobPosition,
  CandidatePendingDocument,
  DocumentBulkImportPreviewRequest,
  DocumentBulkImportPreviewJobResponse,
  DocumentBulkUploadMode,
} from "../types";

type ValidationErrors = Partial<Record<keyof CandidateFormState, string>>;

interface CandidateDetailModalProps {
  mode: "create" | "detail";
  registrationMode: "single" | "bulk";
  onRegistrationModeChange: (mode: "single" | "bulk") => void;
  documentBulkPreview: DocumentBulkImportPreviewJobResponse | null;
  isDocumentBulkPreviewing: boolean;
  isDocumentBulkImporting: boolean;
  detail: CandidateDetailResponse | null;
  form: CandidateFormState;
  validationErrors: ValidationErrors;
  pendingDocuments: CandidatePendingDocument[];
  activeDocumentActionId: number | null;
  isSaving: boolean;
  isDetailLoading: boolean;
  isExtractRefreshing: boolean;
  statusOptions: readonly CandidateApplyStatus[];
  jobPositionOptions: readonly CandidateJobPosition[];
  documentTypeOptions: readonly CandidateDocumentType[];
  onFieldChange: <K extends keyof CandidateFormState>(
    key: K,
    value: CandidateFormState[K],
  ) => void;
  onSave: () => void;
  onBack: () => void;
  onDelete: () => void;
  onAddFiles: (files: FileList | File[] | null) => void;
  onPendingDocumentTypeChange: (
    pendingId: string,
    documentType: CandidateDocumentType,
  ) => void;
  onPendingDocumentRemove: (pendingId: string) => void;
  onDocumentDownload: (document: CandidateDocumentResponse) => void;
  onExistingDocumentDelete: (document: CandidateDocumentResponse) => void;
  onExistingDocumentReplace: (
    document: CandidateDocumentResponse,
    file: File | null,
  ) => void;
  onOpenDocument: (document: CandidateDocumentResponse) => void;
  onDocumentBulkPreview: (request: DocumentBulkImportPreviewRequest) => void;
  onDocumentBulkConfirmImport: (selectedRowIds: string[]) => void;
}

const fieldClassName =
  "mt-2 h-11 w-full rounded-2xl border border-slate-200 bg-white px-4 text-slate-900 outline-none transition focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10";

const pendingCardClassName =
  "grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 md:grid-cols-[minmax(0,1fr)_220px_auto] md:items-center";

const JOB_POSITION_LABEL: Record<string, string> = {
  STRATEGY_PLANNING: "기획·전략",
  HR: "인사·HR",
  MARKETING: "마케팅·광고·MD",
  AI_DEV_DATA: "AI·개발·데이터",
  SALES: "영업",
};

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

function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`;
}

const DOCUMENT_BULK_STATUS_LABEL: Record<string, string> = {
  QUEUED: "대기 중",
  RUNNING: "처리 중",
  SUCCESS: "완료",
  PARTIAL_SUCCESS: "일부 완료",
  FAILED: "실패",
  RETRYING: "재시도 중",
  CANCELLED: "취소됨",
};

const DOCUMENT_BULK_ROW_STATUS_LABEL: Record<string, string> = {
  READY: "등록 가능",
  NEEDS_REVIEW: "검토 필요",
  INVALID: "등록 불가",
};

const DOCUMENT_TYPE_LABEL: Record<string, string> = {
  RESUME: "이력서",
  PORTFOLIO: "포트폴리오",
  COVER_LETTER: "자기소개서",
  CAREER_DESCRIPTION: "경력기술서",
  ROLE_PROFILE: "직무 프로필",
};

const EXTRACT_SOURCE_LABEL: Record<string, string> = {
  DIGITAL_TEXT: "디지털 텍스트",
  TEXT: "텍스트",
  OCR: "OCR",
  PDF: "PDF",
  DOCX: "워드 문서",
  HWP: "한글 문서",
  HWPX: "한글 문서",
};

function formatBulkStatus(value?: string | null) {
  if (!value) {
    return "-";
  }

  return DOCUMENT_BULK_STATUS_LABEL[value] ?? value;
}

function formatBulkRowStatus(value: string) {
  return DOCUMENT_BULK_ROW_STATUS_LABEL[value] ?? "확인 필요";
}

function formatDocumentType(value?: string | null) {
  if (!value) {
    return "-";
  }

  return DOCUMENT_TYPE_LABEL[value] ?? "기타 문서";
}

function formatExtractSource(value?: string | null) {
  if (!value) {
    return "-";
  }

  return EXTRACT_SOURCE_LABEL[value] ?? "자동 감지";
}

function formatExtractStrategy(value?: string | null) {
  if (!value) {
    return "-";
  }

  if (value.toLowerCase().includes("ocr")) {
    return "OCR 추출";
  }

  if (value.toLowerCase().includes("text")) {
    return "텍스트 추출";
  }

  if (value.toLowerCase().includes("pdf")) {
    return "PDF 추출";
  }

  return "자동 추출";
}

function formatBulkStep(value?: string | null) {
  if (!value) {
    return "";
  }

  const groupProgress = value.match(/^preview_processing_group_(\d+)_of_(\d+)$/);
  if (groupProgress) {
    return `그룹 처리 중 (${groupProgress[1]}/${groupProgress[2]})`;
  }

  const stepLabels: Record<string, string> = {
    preview_job_created: "미리보기 작업 생성됨",
    preview_grouping_completed: "문서 그룹 분류 완료",
    preview_completed: "미리보기 완료",
    preview_failed: "미리보기 실패",
    preview_staging_files: "문서 임시 저장 중",
    preview_extracting_documents: "문서 내용 추출 중",
    preview_inferring_profile: "지원자 정보 추론 중",
  };

  return stepLabels[value] ?? "처리 중";
}

function formatBulkSelectedFiles(mode: DocumentBulkUploadMode, zipFile: File | null, files: File[]) {
  if (mode === "ZIP") {
    return zipFile ? [zipFile.name] : [];
  }
  return files.map((file) => file.name);
}

export function CandidateDetailModal({
  mode,
  registrationMode,
  onRegistrationModeChange,
  documentBulkPreview,
  isDocumentBulkPreviewing,
  isDocumentBulkImporting,
  detail,
  form,
  validationErrors,
  pendingDocuments,
  activeDocumentActionId,
  isSaving,
  isDetailLoading,
  isExtractRefreshing,
  statusOptions,
  jobPositionOptions,
  documentTypeOptions,
  onFieldChange,
  onSave,
  onBack,
  onDelete,
  onAddFiles,
  onPendingDocumentTypeChange,
  onPendingDocumentRemove,
  onDocumentDownload,
  onExistingDocumentDelete,
  onExistingDocumentReplace,
  onOpenDocument,
  onDocumentBulkPreview,
  onDocumentBulkConfirmImport,
}: CandidateDetailModalProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [bulkUploadMode, setBulkUploadMode] = useState<DocumentBulkUploadMode>("ZIP");
  const [bulkZipFile, setBulkZipFile] = useState<File | null>(null);
  const [bulkFiles, setBulkFiles] = useState<File[]>([]);
  const [bulkDefaultJobPosition, setBulkDefaultJobPosition] = useState("");
  const [bulkDefaultApplyStatus, setBulkDefaultApplyStatus] =
    useState<CandidateApplyStatus>("APPLIED");
  const [selectedBulkRowIds, setSelectedBulkRowIds] = useState<string[]>([]);

  const isCreateMode = mode === "create";
  const isBulkCreateMode = isCreateMode && registrationMode === "bulk";
  const isDocumentBulkJobRunning =
    documentBulkPreview?.status === "QUEUED" ||
    documentBulkPreview?.status === "RUNNING" ||
    documentBulkPreview?.status === "RETRYING";
  const title = isCreateMode ? "지원자 신규 등록" : "지원자 상세 정보";
  const remainingDocumentSlots = Math.max(0, 3 - pendingDocuments.length);
  const documents = detail?.documents ?? [];
  const hasPendingExtraction = documents.some(
    (document) => document.extractStatus === "PENDING",
  );
  const pendingExtractionCount = documents.filter(
    (document) => document.extractStatus === "PENDING",
  ).length;
  const successExtractionCount = documents.filter(
    (document) => document.extractStatus === "SUCCESS",
  ).length;
  const failedExtractionCount = documents.filter(
    (document) => document.extractStatus === "FAILED",
  ).length;
  const completedExtractionCount =
    successExtractionCount + failedExtractionCount;
  const isInteractionLocked = hasPendingExtraction || isSaving;
  const canCreateBulkPreview =
    !isDocumentBulkPreviewing &&
    !isDocumentBulkJobRunning &&
    (bulkUploadMode === "ZIP" ? Boolean(bulkZipFile) : bulkFiles.length > 0);
  const bulkSelectedFileNames = formatBulkSelectedFiles(
    bulkUploadMode,
    bulkZipFile,
    bulkFiles,
  );
  const visibleBulkFileNames = bulkSelectedFileNames.slice(0, 10);
  const hiddenBulkFileCount = Math.max(0, bulkSelectedFileNames.length - 10);
  const documentBulkSummary = documentBulkPreview?.summary ?? null;
  const importableBulkRows =
    documentBulkPreview?.rows.filter((row) => row.status === "READY") ?? [];
  const selectedImportableBulkRowIds =
    selectedBulkRowIds.length > 0
      ? selectedBulkRowIds.filter((rowId) =>
          importableBulkRows.some((row) => row.rowId === rowId),
        )
      : importableBulkRows.map((row) => row.rowId);
  const canConfirmBulkImport =
    Boolean(documentBulkPreview) &&
    !isDocumentBulkJobRunning &&
    !isDocumentBulkPreviewing &&
    !isDocumentBulkImporting &&
    selectedImportableBulkRowIds.length > 0;

  return (
    <div className="space-y-6">
      <section className="rounded-[32px] border border-white/70 bg-[var(--panel)] p-7 shadow-[var(--shadow)] backdrop-blur-[14px]">
        <div className="flex flex-col gap-4 border-b border-[var(--line)] pb-5 md:flex-row md:items-start md:justify-between">
          <div className="flex items-start gap-4">
            <button
              type="button"
              className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-slate-200 bg-white text-slate-500 transition hover:bg-slate-50 hover:text-slate-700"
              onClick={onBack}
              aria-label="목록으로 이동"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>

            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-600">
                {isCreateMode ? "Create" : "Detail"}
              </p>
              <h2 className="mt-2 text-2xl font-bold text-[var(--text)]">{title}</h2>
              <p className="mt-2 text-sm text-[var(--muted)]">
                지원자 기본 정보, 지원 직무, 진행 상태와 문서를 한 화면에서 관리합니다.
              </p>
            </div>
          </div>

          {!isCreateMode ? <StatusPill status={form.applyStatus} /> : null}
        </div>

        {isCreateMode ? (
          <div className="mt-5 inline-flex rounded-2xl border border-slate-200 bg-white p-1">
            <button
              type="button"
              className={`h-10 rounded-xl px-4 text-sm font-semibold transition ${
                registrationMode === "single"
                  ? "bg-emerald-500 text-white"
                  : "text-slate-600 hover:bg-slate-50"
              }`}
              onClick={() => onRegistrationModeChange("single")}
            >
              단일 등록
            </button>
            <button
              type="button"
              className={`h-10 rounded-xl px-4 text-sm font-semibold transition ${
                registrationMode === "bulk"
                  ? "bg-emerald-500 text-white"
                  : "text-slate-600 hover:bg-slate-50"
              }`}
              onClick={() => onRegistrationModeChange("bulk")}
            >
              문서 일괄등록
            </button>
          </div>
        ) : null}

        {isBulkCreateMode ? (
          <div className="mt-6 space-y-5">
            <section className="rounded-[28px] border border-white/70 bg-[var(--panel-strong)] p-5">
              <h3 className="text-lg font-bold text-[var(--text)]">
                문서 기반 일괄등록 미리보기
              </h3>
              <p className="mt-1 text-sm text-[var(--muted)]">
                ZIP 또는 다중 파일을 업로드해 지원자 후보를 미리 추출합니다. 현재 단계는 확정 저장 전 검수용입니다.
              </p>

              <div className="mt-4 grid gap-4 lg:grid-cols-[180px_minmax(0,1fr)_220px_180px]">
                <label className="block text-sm font-medium text-slate-700">
                  업로드 방식
                  <select
                    className={fieldClassName}
                    value={bulkUploadMode}
                    disabled={isDocumentBulkPreviewing}
                    onChange={(event) =>
                      setBulkUploadMode(event.target.value as DocumentBulkUploadMode)
                    }
                  >
                    <option value="ZIP">ZIP</option>
                    <option value="FILES">다중 파일</option>
                  </select>
                </label>

                <div className="block text-sm font-medium text-slate-700">
                  문서 파일
                  <label
                    className={`mt-2 flex min-h-36 cursor-pointer flex-col items-center justify-center rounded-3xl border-2 border-dashed px-5 py-6 text-center transition ${
                      isDragOver
                        ? "border-emerald-500 bg-emerald-50"
                        : "border-slate-300 bg-white/80 hover:border-emerald-300 hover:bg-emerald-50/40"
                    } ${isDocumentBulkPreviewing ? "cursor-not-allowed opacity-60" : ""}`}
                    onDragOver={(event) => {
                      event.preventDefault();
                      if (!isDocumentBulkPreviewing) {
                        setIsDragOver(true);
                      }
                    }}
                    onDragEnter={(event) => {
                      event.preventDefault();
                      if (!isDocumentBulkPreviewing) {
                        setIsDragOver(true);
                      }
                    }}
                    onDragLeave={(event) => {
                      event.preventDefault();
                      setIsDragOver(false);
                    }}
                    onDrop={(event) => {
                      event.preventDefault();
                      setIsDragOver(false);
                      if (isDocumentBulkPreviewing) {
                        return;
                      }
                      const selected = Array.from(event.dataTransfer.files);
                      if (bulkUploadMode === "ZIP") {
                        setBulkZipFile(
                          selected.find((file) =>
                            file.name.toLowerCase().endsWith(".zip"),
                          ) ??
                            selected[0] ??
                            null,
                        );
                      } else {
                        setBulkFiles(selected);
                      }
                    }}
                  >
                    <Upload className="h-7 w-7 text-emerald-600" />
                    <span className="mt-3 text-sm font-semibold text-slate-900">
                      파일을 드래그앤드롭하거나 클릭해서 선택하세요.
                    </span>
                    <span className="mt-1 text-xs text-slate-500">
                      {bulkUploadMode === "ZIP"
                        ? "ZIP 파일 1개를 업로드합니다."
                        : "PDF, DOCX, TXT 등 여러 문서를 한 번에 업로드합니다."}
                    </span>
                    <input
                      className="hidden"
                      type="file"
                      accept={
                        bulkUploadMode === "ZIP"
                          ? ".zip"
                          : ".pdf,.doc,.docx,.txt,.hwp,.hwpx"
                      }
                      multiple={bulkUploadMode === "FILES"}
                      disabled={isDocumentBulkPreviewing}
                      onChange={(event) => {
                        const selected = Array.from(event.target.files ?? []);
                        if (bulkUploadMode === "ZIP") {
                          setBulkZipFile(selected[0] ?? null);
                        } else {
                          setBulkFiles(selected);
                        }
                        event.target.value = "";
                      }}
                    />
                  </label>
                  <div className="mt-3 rounded-2xl border border-slate-200 bg-white px-4 py-3">
                    {visibleBulkFileNames.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {visibleBulkFileNames.map((fileName) => (
                          <span
                            key={fileName}
                            className="max-w-[220px] truncate rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700"
                            title={fileName}
                          >
                            {fileName}
                          </span>
                        ))}
                        {hiddenBulkFileCount > 0 ? (
                          <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white">
                            ... 외 {hiddenBulkFileCount}개
                          </span>
                        ) : null}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-500">
                        아직 선택된 파일이 없습니다.
                      </p>
                    )}
                  </div>
                </div>

                <label className="block text-sm font-medium text-slate-700">
                  기본 지원 직무
                  <input
                    className={fieldClassName}
                    value={bulkDefaultJobPosition}
                    disabled={isDocumentBulkPreviewing}
                    onChange={(event) => setBulkDefaultJobPosition(event.target.value)}
                    placeholder="예: 백엔드 개발자"
                  />
                </label>

                <label className="block text-sm font-medium text-slate-700">
                  기본 지원 상태
                  <select
                    className={fieldClassName}
                    value={bulkDefaultApplyStatus}
                    disabled={isDocumentBulkPreviewing}
                    onChange={(event) =>
                      setBulkDefaultApplyStatus(event.target.value as CandidateApplyStatus)
                    }
                  >
                    {Object.entries(CANDIDATE_APPLY_STATUS_LABEL).map(
                      ([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ),
                    )}
                  </select>
                </label>
              </div>

              <div className="mt-5 flex justify-end">
                <div className="flex flex-wrap justify-end gap-3">
                  <button
                    type="button"
                    className="rounded-2xl bg-linear-to-r from-emerald-500 to-teal-500 px-4 py-3 text-sm font-semibold text-white shadow-[0_18px_30px_rgba(16,185,129,0.22)] disabled:cursor-not-allowed disabled:opacity-60"
                    disabled={!canCreateBulkPreview}
                    onClick={() =>
                      onDocumentBulkPreview({
                        mode: bulkUploadMode,
                        zipFile: bulkZipFile,
                        files: bulkFiles,
                        defaultJobPosition: bulkDefaultJobPosition,
                        defaultApplyStatus: bulkDefaultApplyStatus,
                      })
                    }
                  >
                    {isDocumentBulkPreviewing ? "미리보기 생성 중..." : "미리보기 생성"}
                  </button>
                  <button
                    type="button"
                    className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
                    disabled={!canConfirmBulkImport}
                    onClick={() => onDocumentBulkConfirmImport(selectedImportableBulkRowIds)}
                  >
                    {isDocumentBulkImporting
                      ? "확정 등록 중..."
                      : `등록 가능 ${selectedImportableBulkRowIds.length}건 확정 등록`}
                  </button>
                </div>
              </div>
            </section>

            {documentBulkPreview ? (
              <section className="rounded-[28px] border border-white/70 bg-[var(--panel-strong)] p-5">
                <div className="mb-4 rounded-2xl border border-slate-200 bg-white p-4">
                  <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                    <div>
                      <p className="text-xs font-semibold text-slate-500">작업 상태</p>
                      <p className="mt-1 text-sm font-bold text-slate-900">
                        {formatBulkStatus(documentBulkPreview.status)}
                        {documentBulkPreview.currentStep
                          ? ` / ${formatBulkStep(documentBulkPreview.currentStep)}`
                          : ""}
                      </p>
                    </div>
                    <p className="text-sm font-semibold text-slate-900">
                      {documentBulkPreview.progress}%
                    </p>
                  </div>
                  <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-emerald-500 transition-all"
                      style={{
                        width: `${Math.max(0, Math.min(100, documentBulkPreview.progress))}%`,
                      }}
                    />
                  </div>
                  {documentBulkSummary ? (
                    <p className="mt-2 text-xs text-slate-500">
                      총 {documentBulkSummary.totalGroups}개 그룹 중{" "}
                      {documentBulkSummary.processedGroups}개 처리 완료
                    </p>
                  ) : null}
                </div>
                <div className="grid gap-3 md:grid-cols-5">
                  <div className="rounded-2xl border border-slate-200 bg-white p-4">
                    <p className="text-xs font-semibold text-slate-500">작업 ID</p>
                    <p className="mt-1 text-lg font-bold text-slate-900">
                      {documentBulkPreview.jobId}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-white p-4">
                    <p className="text-xs font-semibold text-slate-500">그룹 수</p>
                    <p className="mt-1 text-lg font-bold text-slate-900">
                      {documentBulkSummary?.totalGroups ?? 0}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
                    <p className="text-xs font-semibold text-emerald-700">등록 가능</p>
                    <p className="mt-1 text-lg font-bold text-emerald-900">
                      {documentBulkSummary?.readyCount ?? 0}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
                    <p className="text-xs font-semibold text-amber-700">검토 필요</p>
                    <p className="mt-1 text-lg font-bold text-amber-900">
                      {documentBulkSummary?.needsReviewCount ?? 0}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4">
                    <p className="text-xs font-semibold text-rose-700">등록 불가</p>
                    <p className="mt-1 text-lg font-bold text-rose-900">
                      {documentBulkSummary?.invalidCount ?? 0}
                    </p>
                  </div>
                </div>

                <div className="mt-4 overflow-x-auto rounded-2xl border border-slate-200 bg-white">
                  <table className="w-full border-collapse text-sm">
                    <thead className="bg-slate-50">
                      <tr>
                        {[
                          "상태",
                          "선택",
                          "그룹",
                          "이름",
                          "이메일",
                          "전화번호",
                          "생년월일",
                          "직무",
                          "문서",
                          "문서 파싱",
                          "신뢰도",
                          "비고",
                        ].map((label) => (
                          <th
                            key={label}
                            className="border-b border-slate-200 px-3 py-3 text-left font-bold text-slate-500"
                          >
                            {label}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {documentBulkPreview.rows.map((row) => (
                        <tr key={row.rowId} className="align-top">
                          <td className="border-b border-slate-200 px-3 py-3 font-semibold">
                            {formatBulkRowStatus(row.status)}
                          </td>
                          <td className="border-b border-slate-200 px-3 py-3">
                            <input
                              type="checkbox"
                              className="h-4 w-4"
                              checked={selectedBulkRowIds.includes(row.rowId)}
                              disabled={row.status !== "READY" || isDocumentBulkImporting}
                              onChange={(event) => {
                                setSelectedBulkRowIds((current) =>
                                  event.target.checked
                                    ? [...current, row.rowId]
                                    : current.filter((rowId) => rowId !== row.rowId),
                                );
                              }}
                            />
                          </td>
                          <td className="border-b border-slate-200 px-3 py-3">
                            {row.groupKey}
                          </td>
                          <td className="border-b border-slate-200 px-3 py-3">
                            {row.candidate.name || "-"}
                          </td>
                          <td className="border-b border-slate-200 px-3 py-3">
                            {row.candidate.email || "-"}
                          </td>
                          <td className="border-b border-slate-200 px-3 py-3">
                            {row.candidate.phone || "-"}
                          </td>
                          <td className="border-b border-slate-200 px-3 py-3">
                            {row.candidate.birth_date || "-"}
                          </td>
                          <td className="border-b border-slate-200 px-3 py-3">
                            {row.candidate.job_position
                              ? getJobPositionLabel(row.candidate.job_position)
                              : "-"}
                          </td>
                          <td className="border-b border-slate-200 px-3 py-3">
                            {row.documentCount}
                          </td>
                          <td className="max-w-sm border-b border-slate-200 px-3 py-3">
                            <div className="space-y-2">
                              {row.documents.map((document) => (
                                <details
                                  key={document.storedFileName}
                                  className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2"
                                >
                                  <summary className="cursor-pointer text-xs font-semibold text-slate-700">
                                    {document.originalFileName} ·{" "}
                                    {formatBulkStatus(document.extractStatus)} ·{" "}
                                    {formatPercent(document.extractQualityScore)}
                                  </summary>
                                  <div className="mt-2 space-y-1 text-xs text-slate-600">
                                    <p>문서 유형: {formatDocumentType(document.documentType)}</p>
                                    <p>추출 방식: {formatExtractStrategy(document.extractStrategy)}</p>
                                    <p>원본 유형: {formatExtractSource(document.extractSourceType)}</p>
                                    <p>감지 유형: {formatDocumentType(document.detectedDocumentType)}</p>
                                    <p>추출 글자 수: {document.extractedTextLength.toLocaleString()}자</p>
                                    {document.errorMessage ? <p>오류: {document.errorMessage}</p> : null}
                                    {document.extractedTextPreview ? (
                                      <p className="line-clamp-3">
                                        미리보기: {document.extractedTextPreview}
                                      </p>
                                    ) : null}
                                  </div>
                                </details>
                              ))}
                            </div>
                          </td>
                          <td className="border-b border-slate-200 px-3 py-3">
                            {formatPercent(row.confidenceScore)}
                          </td>
                          <td className="max-w-xs border-b border-slate-200 px-3 py-3">
                            {[...row.errors, ...row.warnings].join(" / ") || "-"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            ) : null}
          </div>
        ) : isDetailLoading ? (
          <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-10 text-center text-sm text-[var(--muted)]">
            지원자 상세 정보를 불러오는 중입니다.
          </div>
        ) : (
          <>

        {hasPendingExtraction ? (
          <div className="mt-5 inline-flex items-center gap-2 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-700">
            <LoaderCircle className="h-4 w-4 animate-spin" />
            <span>
              문서 추출 처리 중입니다. 완료 전까지 수정, 삭제, 추가 업로드가 잠시
              제한됩니다.
            </span>
            {isExtractRefreshing ? <span>상태 확인 중</span> : null}
          </div>
        ) : null}

        {false ? (
          <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-10 text-center text-sm text-[var(--muted)]">
            지원자 상세 정보를 불러오는 중입니다.
          </div>
        ) : (
          <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
            <section className="space-y-6">
              <div className="rounded-[28px] border border-white/70 bg-[var(--panel-strong)] p-5">
                <h3 className="text-lg font-bold text-[var(--text)]">기본 정보</h3>

                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  <label className="block text-sm font-medium text-slate-700">
                    이름
                    <input
                      className={fieldClassName}
                      value={form.name}
                      disabled={isInteractionLocked}
                      onChange={(event) => onFieldChange("name", event.target.value)}
                      placeholder="지원자 이름"
                    />
                    {validationErrors.name ? (
                      <p className="mt-2 text-xs text-rose-600">{validationErrors.name}</p>
                    ) : null}
                  </label>

                  <label className="block text-sm font-medium text-slate-700">
                    이메일
                    <input
                      className={fieldClassName}
                      value={form.email}
                      disabled={isInteractionLocked}
                      onChange={(event) => onFieldChange("email", event.target.value)}
                      placeholder="example@company.com"
                    />
                    {validationErrors.email ? (
                      <p className="mt-2 text-xs text-rose-600">{validationErrors.email}</p>
                    ) : null}
                  </label>

                  <label className="block text-sm font-medium text-slate-700">
                    전화번호
                    <input
                      className={fieldClassName}
                      value={form.phone}
                      disabled={isInteractionLocked}
                      onChange={(event) => onFieldChange("phone", event.target.value)}
                      placeholder="010-0000-0000"
                    />
                    {validationErrors.phone ? (
                      <p className="mt-2 text-xs text-rose-600">{validationErrors.phone}</p>
                    ) : null}
                  </label>

                  <label className="block text-sm font-medium text-slate-700">
                    지원 직무
                    <select
                      className={fieldClassName}
                      value={form.jobPosition}
                      disabled={isInteractionLocked}
                      onChange={(event) =>
                        onFieldChange(
                          "jobPosition",
                          event.target.value,
                        )
                      }
                    >
                      <option value="">선택하세요</option>
                      {jobPositionOptions.map((jobPosition) => (
                        <option key={jobPosition} value={jobPosition}>
                          {JOB_POSITION_LABEL[jobPosition] ?? jobPosition}
                        </option>
                      ))}
                    </select>
                    {validationErrors.jobPosition ? (
                      <p className="mt-2 text-xs text-rose-600">
                        {validationErrors.jobPosition}
                      </p>
                    ) : null}
                  </label>

                  <label className="block text-sm font-medium text-slate-700">
                    생년월일
                    <input
                      type="date"
                      className={fieldClassName}
                      value={form.birthDate}
                      disabled={isInteractionLocked}
                      onChange={(event) => onFieldChange("birthDate", event.target.value)}
                    />
                  </label>
                </div>

                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  <label className="block text-sm font-medium text-slate-700">
                    지원 상태
                    <select
                      className={fieldClassName}
                      value={form.applyStatus}
                      disabled={isInteractionLocked}
                      onChange={(event) =>
                        onFieldChange(
                          "applyStatus",
                          event.target.value as CandidateApplyStatus,
                        )
                      }
                    >
                      {statusOptions.map((status) => (
                        <option key={status} value={status}>
                          {status}
                        </option>
                      ))}
                    </select>
                  </label>

                  {!isCreateMode && detail ? (
                    <div className="mt-4 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
                      <p className="text-xs text-slate-400">등록일</p>
                      <p className="mt-1">{formatDateTime(detail.createdAt)}</p>
                    </div>
                  ) : null}
                </div>
              </div>

              <div className="rounded-[28px] border border-white/70 bg-[var(--panel-strong)] p-5">
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-[var(--text)]">문서 등록</h3>
                    <p className="mt-1 text-sm text-[var(--muted)]">
                      자기소개서, 포트폴리오 등 지원 문서를 최대 3개까지 한 번에
                      등록할 수 있습니다.
                    </p>
                  </div>

                  <label className="inline-flex cursor-pointer items-center gap-2 rounded-2xl bg-linear-to-r from-emerald-500 to-teal-500 px-4 py-3 text-sm font-semibold text-white shadow-[0_18px_30px_rgba(16,185,129,0.22)]">
                    <Upload className="h-4 w-4" />
                    파일 추가
                    <input
                      type="file"
                      className="hidden"
                      multiple
                      disabled={isInteractionLocked}
                      onChange={(event) => {
                        onAddFiles(event.target.files);
                        event.target.value = "";
                      }}
                    />
                  </label>
                </div>

                <div
                  className={`mt-4 rounded-3xl border-2 border-dashed px-5 py-8 text-center transition ${
                    isDragOver
                      ? "border-emerald-500 bg-emerald-50"
                      : "border-slate-300 bg-white/70"
                  }`}
                  onDragOver={(event) => {
                    event.preventDefault();
                    setIsDragOver(true);
                  }}
                  onDragEnter={(event) => {
                    event.preventDefault();
                    setIsDragOver(true);
                  }}
                  onDragLeave={(event) => {
                    event.preventDefault();
                    setIsDragOver(false);
                  }}
                  onDrop={(event) => {
                    event.preventDefault();
                    if (isInteractionLocked) {
                      return;
                    }
                    setIsDragOver(false);
                    onAddFiles(Array.from(event.dataTransfer.files));
                  }}
                >
                  <Upload className="mx-auto h-6 w-6 text-emerald-600" />
                  <p className="mt-3 text-sm font-semibold text-slate-900">
                    파일을 이 영역에 드래그하거나 버튼으로 선택해주세요.
                  </p>
                  <p className="mt-2 text-xs text-slate-500">
                    아래 목록에서 어떤 파일이 업로드될지 바로 확인할 수 있습니다.
                  </p>
                  <p className="mt-2 text-xs font-semibold text-emerald-700">
                    현재 {pendingDocuments.length}개 선택 / 추가 가능 {remainingDocumentSlots}개
                  </p>
                </div>

                {pendingDocuments.length > 0 ? (
                  <div className="mt-4 space-y-3">
                    {pendingDocuments.map((document) => (
                      <div key={document.id} className={pendingCardClassName}>
                        <div className="flex min-w-0 items-start gap-3">
                          <Paperclip className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                          <div className="min-w-0">
                            <p className="truncate text-sm font-semibold text-slate-900">
                              {document.file.name}
                            </p>
                            <p className="mt-1 text-xs text-slate-500">
                              업로드 예정 파일 / {formatFileSize(document.file.size)}
                            </p>
                          </div>
                        </div>

                        <select
                          className="h-11 rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-900"
                          value={document.documentType}
                          disabled={isInteractionLocked}
                          onChange={(event) =>
                            onPendingDocumentTypeChange(
                              document.id,
                              event.target.value as CandidateDocumentType,
                            )
                          }
                        >
                          {documentTypeOptions.map((documentType) => (
                            <option key={documentType} value={documentType}>
                              {documentType}
                            </option>
                          ))}
                        </select>

                        <div className="flex justify-end md:justify-center">
                          <button
                            type="button"
                            className="inline-flex h-11 w-11 items-center justify-center rounded-xl border border-rose-200 bg-rose-50 text-rose-600 transition hover:bg-rose-100"
                            disabled={isInteractionLocked}
                            onClick={() => onPendingDocumentRemove(document.id)}
                            aria-label="파일 제거"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="mt-4 rounded-2xl border border-dashed border-slate-300 bg-white/70 px-4 py-8 text-center text-sm text-[var(--muted)]">
                    아직 추가한 신규 문서가 없습니다.
                  </div>
                )}
              </div>
            </section>

            <section className="rounded-[28px] border border-white/70 bg-[var(--panel-strong)] p-5">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-bold text-[var(--text)]">등록 문서</h3>
                  <p className="mt-1 text-sm text-[var(--muted)]">
                    문서 메타 정보와 추출 상태를 확인하고, 필요하면 상세 페이지로
                    이동할 수 있습니다.
                  </p>
                </div>
                <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-600">
                  {documents.length} files
                </span>
              </div>

              {documents.length > 0 ? (
                <div className="mt-4 grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-600 md:grid-cols-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
                      완료
                    </p>
                    <p className="mt-1 text-base font-semibold text-slate-900">
                      {completedExtractionCount} / {documents.length}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
                      추출 중
                    </p>
                    <p className="mt-1 text-base font-semibold text-amber-600">
                      {pendingExtractionCount}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
                      실패
                    </p>
                    <p className="mt-1 text-base font-semibold text-rose-600">
                      {failedExtractionCount}
                    </p>
                  </div>
                </div>
              ) : null}

              <div className="mt-4 space-y-3">
                {documents.length > 0 ? (
                  documents.map((document) => {
                    const isMutating = activeDocumentActionId === document.id;

                    return (
                      <div
                        key={document.id}
                        className="rounded-2xl border border-slate-200 bg-white p-4"
                      >
                        <div className="flex flex-col gap-4">
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <p className="truncate text-sm font-semibold text-slate-900">
                                {document.originalFileName}
                              </p>
                              <p className="mt-1 text-xs text-slate-500">
                                {document.documentType} / {formatFileSize(document.fileSize)}
                              </p>
                            </div>
                            <StatusPill status={document.extractStatus} />
                          </div>

                          <p className="text-xs text-slate-500">
                            등록일 {formatDateTime(document.createdAt)}
                          </p>

                          {document.extractStatus === "PENDING" ? (
                            <div className="inline-flex items-center gap-2 rounded-xl bg-amber-50 px-3 py-2 text-xs font-medium text-amber-700">
                              <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
                              <span>
                                추출 처리 중입니다. 완료되면 상태가 자동으로 갱신됩니다.
                              </span>
                            </div>
                          ) : null}

                          <div className="flex flex-wrap items-center gap-2">
                            <button
                              type="button"
                              className="inline-flex h-10 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 text-sm font-semibold text-slate-700 hover:bg-slate-100"
                              onClick={() => onOpenDocument(document)}
                            >
                              <FileText className="h-4 w-4" />
                              문서 상세
                            </button>

                            <button
                              type="button"
                              className="inline-flex h-10 items-center justify-center gap-2 rounded-xl border border-sky-200 bg-sky-50 px-3 text-sm font-semibold text-sky-700 hover:bg-sky-100"
                              onClick={() => onDocumentDownload(document)}
                            >
                              <Download className="h-4 w-4" />
                              다운로드
                            </button>

                            <label className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-700 transition hover:bg-emerald-100">
                              <RefreshCcw className="h-4 w-4" />
                              {isMutating ? "교체 중..." : "파일 교체"}
                              <input
                                type="file"
                                className="hidden"
                                disabled={isInteractionLocked}
                                onChange={(event) => {
                                  const nextFile = event.target.files?.[0] ?? null;
                                  onExistingDocumentReplace(document, nextFile);
                                  event.target.value = "";
                                }}
                              />
                            </label>

                            <button
                              type="button"
                              className="inline-flex h-10 items-center justify-center gap-2 rounded-xl border border-rose-200 bg-rose-50 px-3 text-sm font-semibold text-rose-700 transition hover:bg-rose-100 disabled:cursor-not-allowed disabled:opacity-60"
                              onClick={() => onExistingDocumentDelete(document)}
                              disabled={isInteractionLocked}
                            >
                              <Trash2 className="h-4 w-4" />
                              삭제
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="rounded-2xl border border-dashed border-slate-300 bg-white/70 px-4 py-10 text-center text-sm text-[var(--muted)]">
                    {isCreateMode
                      ? "지원자를 먼저 저장하면 등록된 문서가 여기에 표시됩니다."
                      : "등록된 문서가 없습니다."}
                  </div>
                )}
              </div>
            </section>
          </div>
        )}
          </>
        )}

        {!isBulkCreateMode ? (
        <div className="mt-6 flex flex-wrap justify-between gap-3 border-t border-[var(--line)] pt-5">
          <div>
            {!isCreateMode && detail ? (
              <button
                type="button"
                className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700"
                onClick={onDelete}
                disabled={isInteractionLocked}
              >
                지원자 삭제
              </button>
            ) : null}
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700"
              onClick={onBack}
              disabled={isSaving}
            >
              목록으로
            </button>
            <button
              type="button"
              className="rounded-2xl bg-linear-to-r from-emerald-500 to-teal-500 px-4 py-3 text-sm font-semibold text-white shadow-[0_18px_30px_rgba(16,185,129,0.22)] disabled:cursor-not-allowed disabled:opacity-60"
              onClick={onSave}
              disabled={isInteractionLocked || isDetailLoading}
            >
              {isSaving ? "저장 중..." : isCreateMode ? "지원자 등록" : "변경사항 저장"}
            </button>
          </div>
        </div>
        ) : null}
      </section>
    </div>
  );
}
