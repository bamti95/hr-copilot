import { useState } from "react";
import type {
  DepartmentRealityFormState,
  DepartmentRealityQuestionId,
  DepartmentRealityQuestionState,
} from "../types";
import { DEPARTMENT_REALITY_QUESTIONS } from "../utils/departmentRealityPresets";

interface DepartmentRealitySectionProps {
  value: DepartmentRealityFormState;
  onChange: (next: DepartmentRealityFormState) => void;
  disabled?: boolean;
}

const checkboxRowClass =
  "flex cursor-pointer items-start gap-3 rounded-xl border border-transparent px-2 py-2 transition hover:border-[var(--line)] hover:bg-[var(--panel)]/80";

function newCustomId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return `custom-${crypto.randomUUID()}`;
  }
  return `custom-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function toggleSelectedId(selectedIds: string[], id: string): string[] {
  if (selectedIds.includes(id)) {
    return selectedIds.filter((x) => x !== id);
  }
  return [...selectedIds, id];
}

function updateQuestion(
  prev: DepartmentRealityFormState,
  questionId: DepartmentRealityQuestionId,
  nextBlock: DepartmentRealityQuestionState,
): DepartmentRealityFormState {
  return { ...prev, [questionId]: nextBlock };
}

export function DepartmentRealitySection({
  value,
  onChange,
  disabled = false,
}: DepartmentRealitySectionProps) {
  const [addOpenFor, setAddOpenFor] = useState<DepartmentRealityQuestionId | null>(null);
  const [draft, setDraft] = useState("");

  const patchQuestion = (questionId: DepartmentRealityQuestionId, block: DepartmentRealityQuestionState) => {
    onChange(updateQuestion(value, questionId, block));
  };

  const handleToggle = (questionId: DepartmentRealityQuestionId, optionId: string) => {
    if (disabled) {
      return;
    }
    const block = value[questionId];
    patchQuestion(questionId, {
      ...block,
      selectedIds: toggleSelectedId(block.selectedIds, optionId),
    });
  };

  const handleAddCustom = (questionId: DepartmentRealityQuestionId) => {
    const trimmed = draft.trim();
    if (!trimmed || disabled) {
      return;
    }
    const id = newCustomId();
    const block = value[questionId];
    patchQuestion(questionId, {
      customItems: [...block.customItems, { id, text: trimmed }],
      selectedIds: [...block.selectedIds, id],
    });
    setDraft("");
    setAddOpenFor(null);
  };

  const handleRemoveCustom = (questionId: DepartmentRealityQuestionId, customId: string) => {
    if (disabled) {
      return;
    }
    const block = value[questionId];
    patchQuestion(questionId, {
      customItems: block.customItems.filter((c) => c.id !== customId),
      selectedIds: block.selectedIds.filter((x) => x !== customId),
    });
  };

  return (
    <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)]/60 p-5">
      <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
        3. 부서 실무 상황 설정 (Department Reality - Internal Only)
      </div>
      <p className="mt-2 text-xs leading-relaxed text-[var(--muted)]">
        부서별 실무 문화·환경을 내부 맥락으로만 기록합니다. 여러 보기를 동시에 선택할 수 있습니다.
      </p>

      <div className="mt-5 space-y-8">
        {DEPARTMENT_REALITY_QUESTIONS.map((q) => {
          const block = value[q.id];
          const showAdd = addOpenFor === q.id;

          return (
            <div key={q.id}>
              <div className="text-sm font-semibold text-[var(--text)]">{q.title}</div>
              <div className="mt-3 grid gap-1">
                {q.presets.map((opt) => {
                  const checked = block.selectedIds.includes(opt.id);
                  return (
                    <label key={opt.id} className={checkboxRowClass}>
                      <input
                        type="checkbox"
                        className="mt-1 h-4 w-4 shrink-0 rounded border-[var(--line)] text-[var(--primary)] focus:ring-[var(--primary)]"
                        checked={checked}
                        disabled={disabled}
                        onChange={() => handleToggle(q.id, opt.id)}
                      />
                      <span className="text-sm leading-snug text-[var(--text)]">{opt.label}</span>
                    </label>
                  );
                })}

                {block.customItems.map((item) => {
                  const checked = block.selectedIds.includes(item.id);
                  return (
                    <div key={item.id} className="flex items-start gap-2">
                      <label className={`${checkboxRowClass} flex-1`}>
                        <input
                          type="checkbox"
                          className="mt-1 h-4 w-4 shrink-0 rounded border-[var(--line)] text-[var(--primary)] focus:ring-[var(--primary)]"
                          checked={checked}
                          disabled={disabled}
                          onChange={() => handleToggle(q.id, item.id)}
                        />
                        <span className="text-sm leading-snug text-[var(--text)]">{item.text}</span>
                      </label>
                      <button
                        type="button"
                        className="mt-1 shrink-0 rounded-lg px-2 py-1 text-xs text-[var(--muted)] underline-offset-2 hover:text-rose-600 hover:underline disabled:opacity-40"
                        disabled={disabled}
                        onClick={() => handleRemoveCustom(q.id, item.id)}
                        aria-label="사용자 추가 항목 삭제"
                      >
                        삭제
                      </button>
                    </div>
                  );
                })}
              </div>

              {showAdd ? (
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <input
                    className="min-h-10 min-w-[200px] flex-1 rounded-xl border border-[var(--line)] bg-[var(--panel-strong)] px-3 py-2 text-sm text-[var(--text)] outline-none transition focus:border-[var(--primary)]"
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    disabled={disabled}
                    placeholder="추가할 설명을 입력하세요"
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        handleAddCustom(q.id);
                      }
                    }}
                  />
                  <button
                    type="button"
                    className="inline-flex h-10 items-center justify-center rounded-xl border border-transparent bg-[var(--primary)] px-4 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
                    disabled={disabled || !draft.trim()}
                    onClick={() => handleAddCustom(q.id)}
                  >
                    추가
                  </button>
                  <button
                    type="button"
                    className="inline-flex h-10 items-center justify-center rounded-xl border border-[var(--line)] bg-[var(--panel-strong)] px-3 text-sm font-medium text-[var(--text)] disabled:opacity-50"
                    disabled={disabled}
                    onClick={() => {
                      setAddOpenFor(null);
                      setDraft("");
                    }}
                  >
                    취소
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  className="mt-3 inline-flex h-9 w-9 items-center justify-center rounded-xl border border-dashed border-[var(--line)] text-lg font-semibold text-[var(--primary)] transition hover:border-[var(--primary)] hover:bg-[var(--panel)] disabled:opacity-40"
                  disabled={disabled}
                  onClick={() => {
                    setAddOpenFor(q.id);
                    setDraft("");
                  }}
                  aria-label="보기 추가"
                  title="보기 추가"
                >
                  +
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
