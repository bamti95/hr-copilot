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
import type {
  CandidateApplyStatus,
  CandidateDetailResponse,
  CandidateDocumentResponse,
  CandidateDocumentType,
  CandidateFormState,
  CandidatePendingDocument,
} from "../types";

type ValidationErrors = Partial<Record<keyof CandidateFormState, string>>;

interface CandidateDetailModalProps {
  mode: "create" | "detail";
  detail: CandidateDetailResponse | null;
  form: CandidateFormState;
  validationErrors: ValidationErrors;
  pendingDocuments: CandidatePendingDocument[];
  activeDocumentActionId: number | null;
  isSaving: boolean;
  isDetailLoading: boolean;
  isExtractRefreshing: boolean;
  statusOptions: readonly CandidateApplyStatus[];
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
}

const fieldClassName =
  "mt-2 h-11 w-full rounded-2xl border border-slate-200 bg-white px-4 text-slate-900 outline-none transition focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10";

const pendingCardClassName =
  "grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 md:grid-cols-[minmax(0,1fr)_220px_auto] md:items-center";

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

export function CandidateDetailModal({
  mode,
  detail,
  form,
  validationErrors,
  pendingDocuments,
  activeDocumentActionId,
  isSaving,
  isDetailLoading,
  isExtractRefreshing,
  statusOptions,
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
}: CandidateDetailModalProps) {
  const [isDragOver, setIsDragOver] = useState(false);

  const isCreateMode = mode === "create";
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
                기본 정보와 지원 문서를 한 화면에서 정리하고, 문서 상세 페이지로 이어서 확인할 수 있습니다.
              </p>
            </div>
          </div>

          {!isCreateMode ? <StatusPill status={form.applyStatus} /> : null}
        </div>

        {hasPendingExtraction ? (
          <div className="mt-5 inline-flex items-center gap-2 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-700">
            <LoaderCircle className="h-4 w-4 animate-spin" />
            <span>문서 추출 처리 중입니다. 완료될 때까지 수정, 삭제, 재업로드가 잠시 잠깁니다.</span>
            {isExtractRefreshing ? <span>· 상태 확인 중</span> : null}
          </div>
        ) : null}

        {isDetailLoading ? (
          <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-10 text-center text-sm text-[var(--muted)]">
            지원자 상세 정보를 불러오는 중입니다.
          </div>
        ) : (
          <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
            <section className="space-y-6">
              <div className="rounded-[28px] border border-white/70 bg-[var(--panel-strong)] p-5">
                <h3 className="text-lg font-bold text-(--text)">기본 정보</h3>

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
                        onFieldChange("applyStatus", event.target.value as CandidateApplyStatus)
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
                    <h3 className="text-lg font-bold text-(--text)">문서 등록</h3>
                    <p className="mt-1 text-sm text-(--muted)">
                      자기소개서, 포트폴리오 등 지원 문서를 최대 3개까지 한 번에 등록할 수 있습니다.
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
                    저장 전 아래 목록에서 어떤 파일이 업로드될지 바로 확인할 수 있습니다.
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
                              업로드 예정 파일 · {formatFileSize(document.file.size)}
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
                    문서 메타 정보를 보고, 필요하면 상세 페이지에서 추출 텍스트까지 확인할 수 있습니다.
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
                                {document.documentType} · {formatFileSize(document.fileSize)}
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
                              <span>추출 처리 중입니다. 완료되면 상태가 자동으로 갱신됩니다.</span>
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
      </section>
    </div>
  );
}
