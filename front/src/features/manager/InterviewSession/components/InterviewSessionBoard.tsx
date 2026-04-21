import { Pagination } from "../../../../common/components/Pagination";
import type {
  InterviewSessionCandidateOption,
  InterviewSessionFormState,
  InterviewSessionListResponse,
  InterviewSessionResponse,
} from "../types";

interface InterviewSessionBoardProps {
  data: InterviewSessionListResponse;
  candidateOptions: InterviewSessionCandidateOption[];
  formMode: "create" | "edit" | null;
  editingSessionId: number | null;
  form: InterviewSessionFormState;
  validationErrors: Partial<Record<keyof InterviewSessionFormState, string>>;
  isLoading: boolean;
  isSaving: boolean;
  pageSize: number;
  candidateFilterId: string;
  targetJobInput: string;
  onCandidateFilterChange: (value: string) => void;
  onTargetJobInputChange: (value: string) => void;
  onSearchSubmit: () => void;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  onCreate: () => void;
  onEdit: (sessionId: number) => void;
  onDelete: (row: InterviewSessionResponse) => void;
  onCloseForm: () => void;
  onSave: () => void;
  onFormChange: <K extends keyof InterviewSessionFormState>(
    key: K,
    value: InterviewSessionFormState[K],
  ) => void;
}

const inputClassName =
  "h-12 w-full rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] px-4 text-[var(--text)] outline-none transition focus:border-[var(--primary)]";

const buttonClassName =
  "inline-flex h-10 items-center justify-center rounded-xl border px-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50";

function formatDateTime(value: string | null) {
  return value ? value.replace("T", " ").slice(0, 16) : "-";
}

export function InterviewSessionBoard({
  data,
  candidateOptions,
  formMode,
  editingSessionId,
  form,
  validationErrors,
  isLoading,
  isSaving,
  pageSize,
  candidateFilterId,
  targetJobInput,
  onCandidateFilterChange,
  onTargetJobInputChange,
  onSearchSubmit,
  onPageChange,
  onPageSizeChange,
  onCreate,
  onEdit,
  onDelete,
  onCloseForm,
  onSave,
  onFormChange,
}: InterviewSessionBoardProps) {
  return (
    <div className="space-y-6">
      <section className="rounded-[32px] border border-white/70 bg-[var(--panel)] p-7 shadow-[var(--shadow)] backdrop-blur-[14px]">
        <div className="mb-5">
          <h2 className="m-0 text-2xl font-bold text-[var(--text)]">
            인터뷰 세션 관리
          </h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            조건별로 인터뷰 세션을 조회하고, 필요한 경우 새 세션을 생성하거나 기존 세션 정보를 수정합니다.
          </p>
        </div>

        <div className="mb-4 grid gap-3 rounded-[24px] border border-white/70 bg-[var(--panel-strong)] p-4 xl:grid-cols-[220px_minmax(0,1fr)_140px_auto_auto] xl:items-end">
          <label className="text-sm font-medium text-[var(--text)]">
            지원자
            <select
              className={`${inputClassName} mt-2`}
              value={candidateFilterId}
              onChange={(event) => onCandidateFilterChange(event.target.value)}
            >
              <option value="">전체 지원자</option>
              {candidateOptions.map((candidate) => (
                <option key={candidate.id} value={candidate.id}>
                  {candidate.name} ({candidate.email})
                </option>
              ))}
            </select>
          </label>

          <label className="text-sm font-medium text-[var(--text)]">
            목표 직무
            <input
              className={`${inputClassName} mt-2`}
              value={targetJobInput}
              onChange={(event) => onTargetJobInputChange(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  onSearchSubmit();
                }
              }}
              placeholder="예: BACKEND_DEVELOPER"
            />
          </label>

          <label className="text-sm font-medium text-[var(--text)]">
            페이지 크기
            <select
              className={`${inputClassName} mt-2`}
              value={pageSize}
              onChange={(event) => onPageSizeChange(Number(event.target.value))}
            >
              {[10, 20, 50].map((size) => (
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
            disabled={isLoading || isSaving}
          >
            검색
          </button>

          <button
            type="button"
            className={`${buttonClassName} border-transparent bg-[var(--primary)] px-4 text-white hover:opacity-90`}
            onClick={onCreate}
            disabled={isLoading || isSaving}
          >
            신규 생성
          </button>
        </div>

        <div className="mb-4 text-right text-sm text-[var(--muted)]">
          총 {data.paging.totalCount}건 / {Math.max(data.paging.totalPages, 1)} 페이지
        </div>

        <div className="overflow-x-auto rounded-[24px] border border-white/70">
          <table className="w-full border-collapse">
            <thead className="bg-white/60">
              <tr>
                {["ID", "지원자", "목표 직무", "난이도", "생성일", "생성자", "액션"].map(
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
              {data.items.map((row) => {
                const isEditing = editingSessionId === row.id;

                return (
                  <tr
                    key={row.id}
                    className={isEditing ? "bg-emerald-50/60" : "transition hover:bg-slate-50/70"}
                  >
                    <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">{row.id}</td>
                    <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">{row.candidateName}</td>
                    <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">{row.targetJob}</td>
                    <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">
                      {row.difficultyLevel ?? "-"}
                    </td>
                    <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">
                      {formatDateTime(row.createdAt)}
                    </td>
                    <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">
                      {row.createdBy ?? "-"}
                    </td>
                    <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">
                      <div className="flex flex-wrap gap-2">
                        <button
                          type="button"
                          className={`${buttonClassName} border-sky-200 bg-sky-50 text-sky-700 hover:bg-sky-100`}
                          onClick={() => onEdit(row.id)}
                          disabled={isLoading || isSaving}
                        >
                          수정
                        </button>
                        <button
                          type="button"
                          className={`${buttonClassName} border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100`}
                          onClick={() => onDelete(row)}
                          disabled={isLoading || isSaving}
                        >
                          삭제
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}

              {data.items.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    className="px-3 py-10 text-center text-sm text-[var(--muted)]"
                  >
                    조회된 인터뷰 세션이 없습니다.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>

        <Pagination paging={data.paging} onPageChange={onPageChange} />
      </section>

      {formMode ? (
        <section className="rounded-[32px] border border-white/70 bg-[var(--panel)] p-7 shadow-[var(--shadow)] backdrop-blur-[14px]">
          <div className="mb-5 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="m-0 text-2xl font-bold text-[var(--text)]">
                {formMode === "create" ? "인터뷰 세션 생성" : "인터뷰 세션 수정"}
              </h2>
              <p className="mt-2 text-sm text-[var(--muted)]">
                세션 생성 시에는 지원자를 함께 선택하고, 수정 시에는 목표 직무와 난이도 정보를 변경할 수 있습니다.
              </p>
            </div>

            <button
              type="button"
              className={`${buttonClassName} border-[var(--line)] bg-[var(--panel-strong)] text-[var(--text)] hover:bg-[var(--panel)]`}
              onClick={onCloseForm}
              disabled={isSaving}
            >
              닫기
            </button>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <label className="text-sm font-medium text-[var(--text)]">
              지원자
              <select
                className={`${inputClassName} mt-2`}
                value={form.candidateId}
                onChange={(event) => onFormChange("candidateId", event.target.value)}
                disabled={formMode === "edit" || isSaving}
              >
                <option value="">지원자를 선택하세요</option>
                {candidateOptions.map((candidate) => (
                  <option key={candidate.id} value={candidate.id}>
                    {candidate.name} ({candidate.email})
                  </option>
                ))}
              </select>
              {validationErrors.candidateId ? (
                <span className="mt-2 block text-xs text-rose-600">
                  {validationErrors.candidateId}
                </span>
              ) : null}
            </label>

            <label className="text-sm font-medium text-[var(--text)]">
              난이도
              <select
                className={`${inputClassName} mt-2`}
                value={form.difficultyLevel}
                onChange={(event) => onFormChange("difficultyLevel", event.target.value)}
                disabled={isSaving}
              >
                <option value="">선택 안 함</option>
                {["JUNIOR", "INTERMEDIATE", "SENIOR"].map((level) => (
                  <option key={level} value={level}>
                    {level}
                  </option>
                ))}
              </select>
              {validationErrors.difficultyLevel ? (
                <span className="mt-2 block text-xs text-rose-600">
                  {validationErrors.difficultyLevel}
                </span>
              ) : null}
            </label>

            <label className="text-sm font-medium text-[var(--text)] md:col-span-2">
              목표 직무
              <input
                className={`${inputClassName} mt-2`}
                value={form.targetJob}
                onChange={(event) => onFormChange("targetJob", event.target.value)}
                disabled={isSaving}
                placeholder="예: BACKEND_DEVELOPER"
              />
              {validationErrors.targetJob ? (
                <span className="mt-2 block text-xs text-rose-600">
                  {validationErrors.targetJob}
                </span>
              ) : null}
            </label>
          </div>

          <div className="mt-6 flex flex-wrap justify-end gap-3">
            <button
              type="button"
              className={`${buttonClassName} border-[var(--line)] bg-[var(--panel-strong)] text-[var(--text)] hover:bg-[var(--panel)]`}
              onClick={onCloseForm}
              disabled={isSaving}
            >
              취소
            </button>
            <button
              type="button"
              className={`${buttonClassName} border-transparent bg-[var(--primary)] px-4 text-white hover:opacity-90`}
              onClick={onSave}
              disabled={isSaving}
            >
              {isSaving ? "저장 중..." : formMode === "create" ? "신규 생성" : "수정 저장"}
            </button>
          </div>
        </section>
      ) : null}
    </div>
  );
}
