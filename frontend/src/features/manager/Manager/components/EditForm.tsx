import { X } from "lucide-react";
import { StatusPill } from "../../../../common/components/StatusPill";
import type { ManagerFormState } from "../types";
import { getRoleLabel, getStatusLabel } from "./managerLabels";

type FormMode = "create" | "edit" | null;

type ValidationErrors = Partial<Record<keyof ManagerFormState, string>>;

interface EditFormProps {
  isOpen: boolean;
  formMode: FormMode;
  form: ManagerFormState;
  validationErrors: ValidationErrors;
  isSaving: boolean;
  roleOptions: readonly string[];
  statusOptions: readonly string[];
  onFormChange: <K extends keyof ManagerFormState>(key: K, value: ManagerFormState[K]) => void;
  onSave: () => void;
  onCancel: () => void;
}

const fieldClassName =
  "mt-2 h-11 w-full rounded-2xl border border-slate-200 bg-white px-4 text-slate-900 outline-none transition focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10";

function getStatusActionLabel(status: string) {
  return status === "ACTIVE" ? "비활성화" : "활성화";
}

export function EditForm({
  isOpen,
  formMode,
  form,
  validationErrors,
  isSaving,
  roleOptions,
  statusOptions,
  onFormChange,
  onSave,
  onCancel,
}: EditFormProps) {
  if (!isOpen || !formMode) {
    return null;
  }

  const formTitle = formMode === "create" ? "신규 관리자 등록" : "관리자 정보 수정";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="relative max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-3xl border border-white/70 bg-[var(--panel)] p-7 shadow-2xl">
        <div className="mb-5 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-600">
              {formMode === "create" ? "Create" : "Edit"}
            </p>
            <h2 className="mt-2 text-2xl font-bold text-[var(--text)]">{formTitle}</h2>
            <p className="mt-2 text-sm text-[var(--muted)]">
              필수 입력값과 형식을 검증한 뒤 저장됩니다.
            </p>
          </div>

          <div className="flex items-center gap-4 self-end md:self-start">
            <StatusPill status={form.status} />
            <button
              type="button"
              className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-slate-200 bg-white text-slate-400 transition-colors hover:bg-slate-50 hover:text-slate-600"
              onClick={onCancel}
              disabled={isSaving}
              aria-label="닫기"
            >
              <X size={22} />
            </button>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <label className="block text-sm font-medium text-slate-700">
            로그인 ID
            <input
              className={fieldClassName}
              value={form.loginId}
              disabled={formMode === "edit"}
              onChange={(event) => onFormChange("loginId", event.target.value)}
              placeholder="영문, 숫자, ., _, - 조합"
            />
            {validationErrors.loginId ? (
              <p className="mt-2 text-xs text-rose-600">{validationErrors.loginId}</p>
            ) : null}
          </label>

          <label className="block text-sm font-medium text-slate-700">
            이름
            <input
              className={fieldClassName}
              value={form.name}
              onChange={(event) => onFormChange("name", event.target.value)}
              placeholder="관리자 이름"
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
              onChange={(event) => onFormChange("email", event.target.value)}
              placeholder="example@company.com"
            />
            {validationErrors.email ? (
              <p className="mt-2 text-xs text-rose-600">{validationErrors.email}</p>
            ) : null}
          </label>

          <label className="block text-sm font-medium text-slate-700">
            비밀번호
            <input
              className={fieldClassName}
              type="password"
              value={form.password}
              onChange={(event) => onFormChange("password", event.target.value)}
              placeholder={formMode === "create" ? "8자 이상 입력" : "변경 시에만 입력"}
            />
            {validationErrors.password ? (
              <p className="mt-2 text-xs text-rose-600">{validationErrors.password}</p>
            ) : null}
          </label>

          <label className="block text-sm font-medium text-slate-700">
            권한
            <select
              className={fieldClassName}
              value={form.roleType}
              onChange={(event) => onFormChange("roleType", event.target.value)}
            >
              {roleOptions.map((role) => (
                <option key={role} value={role}>
                  {getRoleLabel(role)}
                </option>
              ))}
            </select>
            {validationErrors.roleType ? (
              <p className="mt-2 text-xs text-rose-600">{validationErrors.roleType}</p>
            ) : null}
          </label>

          <label className="block text-sm font-medium text-slate-700">
            상태
            <select
              className={fieldClassName}
              value={form.status}
              onChange={(event) => onFormChange("status", event.target.value)}
            >
              {statusOptions.map((status) => (
                <option key={status} value={status}>
                  {getStatusLabel(status)}
                </option>
              ))}
            </select>
            {validationErrors.status ? (
              <p className="mt-2 text-xs text-rose-600">{validationErrors.status}</p>
            ) : null}
          </label>
        </div>

        {formMode === "edit" ? (
          <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
            목록의 상태변경 버튼으로 즉시 {getStatusActionLabel(form.status)} 처리할 수도 있습니다.
          </div>
        ) : null}

        <div className="mt-6 flex flex-wrap gap-3">
          <button
            type="button"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700"
            onClick={onCancel}
            disabled={isSaving}
          >
            취소
          </button>
          <button
            type="button"
            className="rounded-2xl bg-linear-to-r from-emerald-500 to-teal-500 px-4 py-3 text-sm font-semibold text-white shadow-[0_18px_30px_rgba(16,185,129,0.22)] disabled:cursor-not-allowed disabled:opacity-60"
            onClick={onSave}
            disabled={isSaving}
          >
            {isSaving ? "저장 중..." : formMode === "create" ? "관리자 생성" : "수정 저장"}
          </button>
        </div>
      </div>
    </div>
  );
}
