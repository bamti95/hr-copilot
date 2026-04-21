import { useEffect, useState } from "react";
import { getErrorMessage } from "../../../../utils/getErrorMessage";
import { fetchPromptProfileList } from "../../PromptProfile/services/promptProfileService";
import type { PromptProfileResponse } from "../../PromptProfile/types";

interface CandidatePromptProfileActionModalProps {
  open: boolean;
  targetJob: string;
  onClose: () => void;
  onPickExisting: (row: PromptProfileResponse) => void;
  onCreateNew: () => void;
}

const buttonClassName =
  "inline-flex h-10 items-center justify-center rounded-xl border px-4 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50";

export function CandidatePromptProfileActionModal({
  open,
  targetJob,
  onClose,
  onPickExisting,
  onCreateNew,
}: CandidatePromptProfileActionModalProps) {
  const [items, setItems] = useState<PromptProfileResponse[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) {
      setItems([]);
      setSelectedId(null);
      setError("");
      return;
    }

    let active = true;

    const run = async () => {
      try {
        setLoading(true);
        setError("");
        const res = await fetchPromptProfileList({
          page: 1,
          limit: 100,
          targetJob: targetJob.trim(),
        });
        if (!active) {
          return;
        }
        setItems(res.items);
        setSelectedId(res.items[0]?.id ?? null);
      } catch (e) {
        if (!active) {
          return;
        }
        setError(getErrorMessage(e, "프롬프트 프로필 목록을 불러오지 못했습니다."));
        setItems([]);
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    void run();

    return () => {
      active = false;
    };
  }, [open, targetJob]);

  if (!open) {
    return null;
  }

  const handleConfirmExisting = () => {
    const row = items.find((r) => r.id === selectedId);
    if (row) {
      onPickExisting(row);
    }
  };

  return (
    <div
      className="fixed inset-0 z-[90] flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="candidate-prompt-profile-wizard-title"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg rounded-[28px] border border-white/70 bg-[var(--panel)] p-7 shadow-[var(--shadow)]"
        onClick={(e) => e.stopPropagation()}
      >
        <h2
          id="candidate-prompt-profile-wizard-title"
          className="text-lg font-bold text-[var(--text)]"
        >
          프롬프트 프로필
        </h2>
        <p className="mt-2 text-sm text-[var(--muted)]">
          직무「{targetJob}」에 등록된 프로필이 있으면 선택할 수 있습니다. 없으면 신규 등록으로 진행하세요.
        </p>

        {error ? (
          <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
            {error}
          </div>
        ) : null}

        {loading ? (
          <p className="mt-6 text-sm text-[var(--muted)]">불러오는 중…</p>
        ) : items.length > 0 ? (
          <ul className="mt-4 max-h-60 space-y-2 overflow-y-auto rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] p-3">
            {items.map((row) => (
              <li key={row.id}>
                <label className="flex cursor-pointer items-start gap-3 rounded-xl px-2 py-2 hover:bg-white/60">
                  <input
                    type="radio"
                    name="prompt-profile-pick"
                    className="mt-1"
                    checked={selectedId === row.id}
                    onChange={() => setSelectedId(row.id)}
                  />
                  <span className="min-w-0">
                    <span className="font-semibold text-[var(--text)]">{row.profileKey}</span>
                    <span className="mt-0.5 block truncate text-xs text-[var(--muted)]">
                      {row.systemPrompt.slice(0, 120)}
                      {row.systemPrompt.length > 120 ? "…" : ""}
                    </span>
                  </span>
                </label>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-4 text-sm text-[var(--muted)]">이 직무로 등록된 프롬프트 프로필이 없습니다.</p>
        )}

        <div className="mt-6 flex flex-col gap-3 border-t border-[var(--line)] pt-5 sm:flex-row sm:flex-wrap sm:justify-end">
          <button
            type="button"
            className={`${buttonClassName} border-[var(--line)] bg-[var(--panel-strong)] text-[var(--text)] hover:bg-white/80`}
            onClick={onClose}
          >
            닫기
          </button>
          {items.length > 0 ? (
            <button
              type="button"
              className={`${buttonClassName} border-slate-900 bg-slate-900 text-white hover:bg-slate-800`}
              onClick={handleConfirmExisting}
              disabled={selectedId === null}
            >
              선택한 프로필 사용
            </button>
          ) : null}
          <button
            type="button"
            className={`${buttonClassName} border-transparent bg-[var(--primary)] text-white hover:opacity-90`}
            onClick={onCreateNew}
          >
            새로 생성하기
          </button>
        </div>
      </div>
    </div>
  );
}
