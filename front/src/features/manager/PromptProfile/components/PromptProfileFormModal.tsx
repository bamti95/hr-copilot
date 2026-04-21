import { useMemo, type ReactNode } from "react";
import type { PromptProfileFormState } from "../types";
import { buildAgentSystemPrompt } from "../utils/buildAgentSystemPrompt";

export type PromptProfileDialogMode = "closed" | "create" | "edit";

interface PromptProfileFormModalProps {
  mode: PromptProfileDialogMode;
  form: PromptProfileFormState;
  isSaving: boolean;
  formError: string;
  onClose: () => void;
  onFieldChange: <K extends keyof PromptProfileFormState>(
    key: K,
    value: PromptProfileFormState[K],
  ) => void;
  onSubmit: () => void;
}

const fieldClassName =
  "mt-2 min-h-11 w-full rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] px-4 py-2.5 text-[var(--text)] outline-none transition focus:border-[var(--primary)]";

const buttonClassName =
  "inline-flex h-10 items-center justify-center rounded-xl border px-4 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50";

const sectionTitleClass =
  "mt-2 text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]";

function SectionLabel({ children }: { children: ReactNode }) {
  return <div className={sectionTitleClass}>{children}</div>;
}

export function PromptProfileFormModal({
  mode,
  form,
  isSaving,
  formError,
  onClose,
  onFieldChange,
  onSubmit,
}: PromptProfileFormModalProps) {
  const isCreate = mode === "create";
  const composedPreview = useMemo(() => buildAgentSystemPrompt(form), [form]);

  if (mode === "closed") {
    return null;
  }

  const title = isCreate ? "AI 채용 에이전트 · 프로필 등록" : "프롬프트 프로필 수정";

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="prompt-profile-dialog-title"
      onClick={() => {
        if (!isSaving) {
          onClose();
        }
      }}
    >
      <div
        className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-[28px] border border-white/70 bg-[var(--panel)] p-7 shadow-[var(--shadow)]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-6 flex flex-col gap-2 border-b border-[var(--line)] pb-5">
          <h2 id="prompt-profile-dialog-title" className="text-xl font-bold text-[var(--text)]">
            {title}
          </h2>
          <p className="text-sm text-[var(--muted)]">
            {isCreate
              ? "기본 정보·기술 요건을 입력하면 시스템 프롬프트가 자동으로 합성됩니다. Output schema는 유효한 JSON 문자열이어야 합니다."
              : "시스템 프롬프트와 Output schema를 직접 수정할 수 있습니다."}
          </p>
        </div>

        {formError ? (
          <div className="mb-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
            {formError}
          </div>
        ) : null}

        <div className="grid gap-6">
          <label className="text-sm font-medium text-[var(--text)]">
            프로필 키 (고유)
            <input
              className={fieldClassName}
              value={form.profileKey}
              onChange={(e) => onFieldChange("profileKey", e.target.value)}
              disabled={!isCreate || isSaving}
              placeholder="예: BE_JUNIOR_01"
              maxLength={100}
            />
            {!isCreate ? (
              <span className="mt-1 block text-xs text-[var(--muted)]">등록 후에는 변경할 수 없습니다.</span>
            ) : null}
          </label>

          {isCreate ? (
            <>
              <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)]/60 p-5">
                <SectionLabel>1. 기본 정보 (Basic Information)</SectionLabel>
                <div className="mt-4 grid gap-4">
                  <label className="text-sm font-medium text-[var(--text)]">
                    에이전트 명칭
                    <input
                      className={fieldClassName}
                      value={form.agentName}
                      onChange={(e) => onFieldChange("agentName", e.target.value)}
                      disabled={isSaving}
                      placeholder="예: 26년 상반기 AI 서비스팀 분석봇"
                    />
                  </label>
                  <label className="text-sm font-medium text-[var(--text)]">
                    채용 부서
                    <input
                      className={fieldClassName}
                      value={form.department}
                      onChange={(e) => onFieldChange("department", e.target.value)}
                      disabled={isSaving}
                      placeholder="예: 플랫폼 개발본부"
                    />
                  </label>
                  <label className="text-sm font-medium text-[var(--text)]">
                    채용 직무
                    <input
                      className={fieldClassName}
                      value={form.jobTitle}
                      onChange={(e) => onFieldChange("jobTitle", e.target.value)}
                      disabled={isSaving}
                      placeholder="예: 주니어 백엔드 개발자"
                    />
                  </label>
                </div>
              </div>

              <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)]/60 p-5">
                <SectionLabel>2. 기술 및 자격 요건 (Technical Requirements)</SectionLabel>
                <div className="mt-4 grid gap-4">
                  <label className="text-sm font-medium text-[var(--text)]">
                    필수 기술 스택 (Must-have)
                    <input
                      className={fieldClassName}
                      value={form.mustHaveStack}
                      onChange={(e) => onFieldChange("mustHaveStack", e.target.value)}
                      disabled={isSaving}
                      placeholder="Python, FastAPI, PostgreSQL"
                    />
                    <span className="mt-1 block text-xs text-[var(--muted)]">
                      쉼표(,)로 구분해 태그처럼 입력합니다.
                    </span>
                  </label>
                  <label className="text-sm font-medium text-[var(--text)]">
                    우대 기술 스택 (Nice-to-have)
                    <input
                      className={fieldClassName}
                      value={form.niceToHaveStack}
                      onChange={(e) => onFieldChange("niceToHaveStack", e.target.value)}
                      disabled={isSaving}
                      placeholder="Docker, AWS, Redis"
                    />
                    <span className="mt-1 block text-xs text-[var(--muted)]">
                      선택 · 쉼표로 구분
                    </span>
                  </label>
                  <label className="text-sm font-medium text-[var(--text)]">
                    필수 자격 및 학력
                    <input
                      className={fieldClassName}
                      value={form.qualifications}
                      onChange={(e) => onFieldChange("qualifications", e.target.value)}
                      disabled={isSaving}
                      placeholder="예: 정보처리기사, 관련 전공 무관 등"
                    />
                  </label>
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-[var(--text)]">
                  합성될 시스템 프롬프트 (미리보기)
                  <textarea
                    className={`${fieldClassName} mt-2 min-h-[160px] resize-y bg-[var(--panel)] text-sm text-[var(--muted)]`}
                    value={composedPreview}
                    readOnly
                    aria-readonly="true"
                  />
                </label>
              </div>
            </>
          ) : (
            <label className="text-sm font-medium text-[var(--text)]">
              시스템 프롬프트
              <textarea
                className={`${fieldClassName} min-h-[160px] resize-y`}
                value={form.systemPrompt}
                onChange={(e) => onFieldChange("systemPrompt", e.target.value)}
                disabled={isSaving}
                placeholder="역할, 평가 관점, 톤 등을 입력하세요."
              />
            </label>
          )}

          <label className="text-sm font-medium text-[var(--text)]">
            Output schema (JSON 문자열, 선택)
            <textarea
              className={`${fieldClassName} min-h-[100px] resize-y font-mono text-sm`}
              value={form.outputSchema}
              onChange={(e) => onFieldChange("outputSchema", e.target.value)}
              disabled={isSaving}
              placeholder='예: {"questions": [{"question_text": "string"}]}'
            />
          </label>
        </div>

        <div className="mt-8 flex flex-wrap justify-end gap-3 border-t border-[var(--line)] pt-6">
          <button
            type="button"
            className={`${buttonClassName} border-[var(--line)] bg-[var(--panel-strong)] text-[var(--text)] hover:bg-white/80`}
            onClick={onClose}
            disabled={isSaving}
          >
            취소
          </button>
          <button
            type="button"
            className={`${buttonClassName} border-transparent bg-[var(--primary)] text-white hover:opacity-90`}
            onClick={onSubmit}
            disabled={isSaving}
          >
            {isSaving ? "저장 중…" : "저장"}
          </button>
        </div>
      </div>
    </div>
  );
}
