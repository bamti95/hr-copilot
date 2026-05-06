import { Eye, FilePlus2, Pencil, Trash2 } from "lucide-react";
import { Pagination } from "../../../../common/components/Pagination";
import {
  CANDIDATE_JOB_POSITION_OPTIONS,
  getJobPositionLabel,
} from "../../common/candidateJobPosition";
import type {
  InterviewSessionCandidateOption,
  InterviewSessionFormState,
  InterviewSessionListResponse,
  InterviewSessionPromptProfileOption,
} from "../types";

import { formatDateTime } from "../../common/formatDateTime"; 

interface InterviewSessionBoardProps {
  data: InterviewSessionListResponse;
  candidateOptions: InterviewSessionCandidateOption[];
  promptProfileOptions: InterviewSessionPromptProfileOption[];
  formMode: "create" | "edit" | null;
  editingSessionId: number | null;
  form: InterviewSessionFormState;
  validationErrors: Partial<Record<keyof InterviewSessionFormState, string>>;
  isLoading: boolean;
  isSaving: boolean;
  pageSize: number;
  jobFilter: string;
  candidateNameInput: string;
  onJobFilterChange: (value: string) => void;
  onCandidateNameInputChange: (value: string) => void;
  onSearchSubmit: () => void;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  onCreate: () => void;
  onView: (sessionId: number) => void;
  onEdit: (sessionId: number) => void;
  onDelete: (sessionId: number, candidateName: string) => void;
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

const iconButtonClassName =
  "inline-flex h-9 items-center justify-center gap-2 rounded-xl px-3 text-xs font-semibold transition disabled:cursor-not-allowed disabled:opacity-50";

function renderDifficultyTone(value: string | null) {
  if (value === "SENIOR") {
    return "bg-slate-900 text-white";
  }
  if (value === "INTERMEDIATE") {
    return "bg-amber-100 text-amber-900";
  }
  if (value === "JUNIOR") {
    return "bg-sky-100 text-sky-800";
  }
  return "bg-slate-100 text-slate-500";
}

function renderPromptProfileLabel(profile: InterviewSessionPromptProfileOption) {
  if (!profile.targetJob) {
    return `${profile.profileKey} (common)`;
  }
  return `${profile.profileKey} (${getJobPositionLabel(profile.targetJob)})`;
}

export function InterviewSessionBoard({
  data,
  candidateOptions,
  promptProfileOptions,
  formMode,
  editingSessionId,
  form,
  validationErrors,
  isLoading,
  isSaving,
  pageSize,
  jobFilter,
  candidateNameInput,
  onJobFilterChange,
  onCandidateNameInputChange,
  onSearchSubmit,
  onPageChange,
  onPageSizeChange,
  onCreate,
  onView,
  onEdit,
  onDelete,
  onCloseForm,
  onSave,
  onFormChange,
}: InterviewSessionBoardProps) {
  return (
    <div className="space-y-6">
      <section className="rounded-[32px] border border-white/70 bg-[var(--panel)] p-7 shadow-[var(--shadow)] backdrop-blur-[14px]">
        <div className="mb-5 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="m-0 text-2xl font-bold text-[var(--text)]">
              면접 세션 관리
            </h2>
            <p className="mt-2 text-sm text-[var(--muted)]">
              필터 기반 조회, 세션 생성, 모달 중심 상세 확인 흐름을 현재 백엔드 API에
              맞춰 제공합니다.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <span className="inline-flex rounded-full border border-[var(--line)] bg-[var(--panel-strong)] px-3 py-1.5 text-xs font-semibold text-[var(--muted)]">
              총 {data.paging.totalCount}건
            </span>
            <span className="inline-flex rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700">
              모달 상세 보기 지원
            </span>
          </div>
        </div>

        <div className="mb-4 grid gap-3 rounded-[24px] border border-white/70 bg-[var(--panel-strong)] p-4 xl:grid-cols-[220px_minmax(0,1fr)_140px_auto_auto] xl:items-end">
          <label className="text-sm font-medium text-[var(--text)]">
            지원 직무
            <select
              className={`${inputClassName} mt-2`}
              value={jobFilter}
              onChange={(event) => onJobFilterChange(event.target.value)}
            >
              <option value="">전체 직무</option>
              {CANDIDATE_JOB_POSITION_OPTIONS.map((job) => (
                <option key={job.value} value={job.value}>
                  {job.label}
                </option>
              ))}
            </select>
          </label>

          <label className="text-sm font-medium text-[var(--text)]">
            지원자 이름
            <input
              className={`${inputClassName} mt-2`}
              value={candidateNameInput}
              onChange={(event) => onCandidateNameInputChange(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  onSearchSubmit();
                }
              }}
              placeholder="예: 김철수"
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
            세션 생성
          </button>
        </div>

        <div className="mb-4 text-right text-sm text-[var(--muted)]">
          {Math.max(data.paging.page, 1)} / {Math.max(data.paging.totalPages, 1)} 페이지
        </div>

        <div className="overflow-x-auto rounded-[24px] border border-white/70">
          <table className="w-full border-collapse">
            <thead className="bg-white/60">
              <tr>
                {[
                  "세션",
                  "지원자",
                  "목표 직무",
                  "난이도",
                  "생성일",
                  "생성자",
                  "액션",
                ].map((label) => (
                  <th
                    key={label}
                    className="border-b border-[var(--line)] px-3 py-3 text-left text-[0.84rem] font-bold whitespace-nowrap text-[var(--muted)]"
                  >
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.items.map((row) => {
                const isEditing = editingSessionId === row.id;

                return (
                  <tr
                    key={row.id}
                    className={`group transition ${
                      isEditing ? "bg-emerald-50/70" : "hover:bg-slate-50/80"
                    }`}
                  >
                    <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">
                      <button
                        type="button"
                        className="text-left font-semibold text-[var(--text)] underline-offset-4 transition hover:text-[var(--primary)] hover:underline"
                        onClick={() => onView(row.id)}
                        disabled={isSaving}
                      >
                        #{row.id}
                      </button>
                    </td>
                    <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">
                      <button
                        type="button"
                        className="text-left font-semibold text-[var(--text)] transition hover:text-[var(--primary)]"
                        onClick={() => onView(row.id)}
                        disabled={isSaving}
                      >
                        {row.candidateName}
                      </button>
                    </td>
                    <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap text-[var(--text)]">
                      {getJobPositionLabel(row.targetJob)}
                    </td>
                    <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">
                      <span
                        className={`inline-flex rounded-full px-3 py-1 text-xs font-bold ${renderDifficultyTone(
                          row.difficultyLevel,
                        )}`}
                      >
                        {row.difficultyLevel ?? "미설정"}
                      </span>
                    </td>
                    <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap text-sm text-[var(--muted)]">
                      {formatDateTime(row.createdAt)}
                    </td>
                    <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap text-sm text-[var(--muted)]">
                      {row.createdName ?? "-"}
                    </td>
                    <td className="border-b border-[var(--line)] px-3 py-3 whitespace-nowrap">
                      <div className="flex flex-wrap gap-2">
                        <button
                          type="button"
                          className={`${iconButtonClassName} border border-sky-200 bg-sky-50 text-sky-700 hover:bg-sky-100`}
                          onClick={() => onView(row.id)}
                          disabled={isSaving}
                        >
                          <Eye className="h-3.5 w-3.5" />
                          상세
                        </button>
                        <button
                          type="button"
                          className={`${iconButtonClassName} border border-amber-200 bg-amber-50 text-amber-700 hover:bg-amber-100`}
                          onClick={() => onEdit(row.id)}
                          disabled={isSaving}
                        >
                          <Pencil className="h-3.5 w-3.5" />
                          수정
                        </button>
                        <button
                          type="button"
                          className={`${iconButtonClassName} border border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100`}
                          onClick={() => onDelete(row.id, row.candidateName)}
                          disabled={isSaving}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
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
                    조회된 면접 세션이 없습니다.
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
          <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-[var(--line)] bg-[var(--panel-strong)] px-3 py-1 text-xs font-semibold text-[var(--muted)]">
                <FilePlus2 className="h-3.5 w-3.5" />
                {formMode === "create" ? "생성 모드" : "수정 모드"}
              </div>
              <h2 className="mt-3 text-2xl font-bold text-[var(--text)]">
                {formMode === "create"
                  ? "면접 세션 생성"
                  : "면접 세션 수정"}
              </h2>
              <p className="mt-2 text-sm text-[var(--muted)]">
                현재 백엔드 `/interview-sessions` 요청 스펙에 맞춰 입력값을 저장합니다.
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
                <option value="">지원자를 선택해 주세요</option>
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

            <label className="text-sm font-medium text-[var(--text)]">
              프롬프트 프로필
              <select
                className={`${inputClassName} mt-2`}
                value={form.promptProfileId}
                onChange={(event) => onFormChange("promptProfileId", event.target.value)}
                disabled={formMode === "edit" || isSaving}
              >
                <option value="">프롬프트 프로필을 선택해 주세요</option>
                {promptProfileOptions.map((profile) => (
                  <option key={profile.id} value={profile.id}>
                    {renderPromptProfileLabel(profile)}
                  </option>
                ))}
              </select>
              {validationErrors.promptProfileId ? (
                <span className="mt-2 block text-xs text-rose-600">
                  {validationErrors.promptProfileId}
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
              {isSaving
                ? "저장 중..."
                : formMode === "create"
                  ? "세션 생성"
                  : "변경 저장"}
            </button>
          </div>
        </section>
      ) : null}
    </div>
  );
}
