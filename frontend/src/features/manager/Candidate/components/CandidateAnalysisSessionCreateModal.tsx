import { useEffect, useMemo, useState } from "react";
import { getErrorMessage } from "../../../../utils/getErrorMessage";
import { fetchPromptProfileList } from "../../PromptProfile/services/promptProfileService";
import type { DifficultyLevel, PromptProfileOption } from "../types";

interface CandidateAnalysisSessionCreateModalProps {
  open: boolean;
  selectedCount: number;
  targetJob: string;
  isSubmitting: boolean;
  onClose: () => void;
  onConfirm: (payload: {
    difficultyLevel: DifficultyLevel | null;
    promptProfileId: number | null;
    promptProfileSnapshot: Record<string, unknown> | null;
  }) => void;
}

const buttonClassName =
  "inline-flex h-10 items-center justify-center rounded-xl border px-4 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50";

const difficultyOptions: Array<{
  value: DifficultyLevel;
  label: string;
  description: string;
}> = [
  { value: "JUNIOR", label: "JUNIOR", description: "기초 역량 중심" },
  { value: "INTERMEDIATE", label: "INTERMEDIATE", description: "실무 중심" },
  { value: "SENIOR", label: "SENIOR", description: "심화 판단 중심" },
];

const JOB_POSITION_LABEL: Record<string, string> = {
  STRATEGY_PLANNING: "기획·전략",
  HR: "인사·HR",
  MARKETING: "마케팅·광고·MD",
  AI_DEV_DATA: "AI·개발·데이터",
  SALES: "영업",
};

function toPromptProfileOption(row: {
  id: number;
  profileKey: string;
  targetJob: string | null;
  systemPrompt: string;
}): PromptProfileOption {
  return {
    id: row.id,
    profileKey: row.profileKey,
    targetJob: row.targetJob,
    systemPromptPreview: row.systemPrompt.slice(0, 120),
  };
}

function getJobAliases(targetJob: string) {
  const trimmed = targetJob.trim();
  const koreanLabel = JOB_POSITION_LABEL[trimmed];

  return new Set(
    [trimmed, koreanLabel]
      .filter((value): value is string => Boolean(value))
      .map((value) => value.toLowerCase()),
  );
}

function isMatchingPromptProfile(
  profile: PromptProfileOption,
  targetJob: string,
) {
  if (!profile.targetJob) {
    return false;
  }

  const aliases = getJobAliases(targetJob);
  return aliases.has(profile.targetJob.trim().toLowerCase());
}

function getJobPositionLabel(targetJob: string) {
  return JOB_POSITION_LABEL[targetJob] ?? targetJob;
}

export function CandidateAnalysisSessionCreateModal({
  open,
  selectedCount,
  targetJob,
  isSubmitting,
  onClose,
  onConfirm,
}: CandidateAnalysisSessionCreateModalProps) {
  const [items, setItems] = useState<PromptProfileOption[]>([]);
  const [selectedPromptProfileId, setSelectedPromptProfileId] = useState<number | null>(null);
  const [difficultyLevel, setDifficultyLevel] = useState<DifficultyLevel | "">("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) {
      setItems([]);
      setSelectedPromptProfileId(null);
      setDifficultyLevel("");
      setLoading(false);
      setError("");
      return;
    }

    let active = true;

    const run = async () => {
      try {
        setLoading(true);
        setError("");

        const filteredResponse = await fetchPromptProfileList({
          page: 1,
          limit: 100,
          targetJob: targetJob.trim() || undefined,
        });
        if (!active) {
          return;
        }

        let nextItems = filteredResponse.items.map(toPromptProfileOption);

        // Fallback: prompt profiles may have been saved with Korean job labels
        // or without a target_job filterable by the current enum value.
        if (nextItems.length === 0) {
          const unfilteredResponse = await fetchPromptProfileList({
            page: 1,
            limit: 100,
          });
          if (!active) {
            return;
          }

          const unfilteredItems = unfilteredResponse.items.map(toPromptProfileOption);
          const matchedItems = unfilteredItems.filter((item) =>
            isMatchingPromptProfile(item, targetJob),
          );
          const commonItems = unfilteredItems.filter((item) => item.targetJob === null);

          nextItems =
            matchedItems.length > 0
              ? [...matchedItems, ...commonItems.filter((item) => !matchedItems.some((matched) => matched.id === item.id))]
              : unfilteredItems;
        }

        setItems(nextItems);
        setSelectedPromptProfileId(nextItems[0]?.id ?? null);
      } catch (loadError) {
        if (!active) {
          return;
        }
        setItems([]);
        setSelectedPromptProfileId(null);
        setError(
          getErrorMessage(loadError, "프롬프트 프로필 목록을 불러오지 못했습니다."),
        );
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

  const selectedPromptProfile = useMemo(
    () => items.find((item) => item.id === selectedPromptProfileId) ?? null,
    [items, selectedPromptProfileId],
  );

  if (!open) {
    return null;
  }

  const handleConfirm = () => {
    onConfirm({
      difficultyLevel: difficultyLevel || null,
      promptProfileId: selectedPromptProfileId,
      promptProfileSnapshot: selectedPromptProfile
        ? {
            id: selectedPromptProfile.id,
            profileKey: selectedPromptProfile.profileKey,
            targetJob: selectedPromptProfile.targetJob,
            systemPromptPreview: selectedPromptProfile.systemPromptPreview,
          }
        : null,
    });
  };

  return (
    <div
      className="fixed inset-0 z-[90] flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="candidate-analysis-session-create-title"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl rounded-[28px] border border-white/70 bg-[var(--panel)] p-7 shadow-[var(--shadow)]"
        onClick={(event) => event.stopPropagation()}
      >
        <h2
          id="candidate-analysis-session-create-title"
          className="text-lg font-bold text-[var(--text)]"
        >
          분석 세션 생성
        </h2>
        <p className="mt-2 text-sm text-[var(--muted)]">
          선택한 지원자들에 대해 분석 세션만 먼저 생성합니다. 실제 분석 실행은 이후
          단계에서 별도로 진행됩니다.
        </p>

        <div className="mt-5 grid gap-3 rounded-[24px] border border-white/70 bg-[var(--panel-strong)] p-4 sm:grid-cols-2">
          <div className="rounded-2xl border border-[var(--line)] bg-white/70 px-4 py-3">
            <div className="text-xs font-medium text-[var(--muted)]">선택된 지원자</div>
            <div className="mt-1 text-lg font-bold text-[var(--text)]">{selectedCount}명</div>
          </div>
          <div className="rounded-2xl border border-[var(--line)] bg-white/70 px-4 py-3">
            <div className="text-xs font-medium text-[var(--muted)]">선택된 직무</div>
            <div className="mt-1 text-lg font-bold text-[var(--text)]">
              {getJobPositionLabel(targetJob)}
            </div>
          </div>
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <label className="text-sm font-medium text-[var(--text)]">
            난이도
            <select
              className="mt-2 h-12 w-full rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] px-4 text-[var(--text)] outline-none transition focus:border-[var(--primary)]"
              value={difficultyLevel}
              onChange={(event) =>
                setDifficultyLevel(event.target.value as DifficultyLevel | "")
              }
              disabled={isSubmitting}
            >
              <option value="">선택 안 함</option>
              {difficultyOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label} - {option.description}
                </option>
              ))}
            </select>
          </label>

          <label className="text-sm font-medium text-[var(--text)]">
            프롬프트 프로필
            <select
              className="mt-2 h-12 w-full rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] px-4 text-[var(--text)] outline-none transition focus:border-[var(--primary)]"
              value={selectedPromptProfileId ?? ""}
              onChange={(event) =>
                setSelectedPromptProfileId(
                  event.target.value ? Number(event.target.value) : null,
                )
              }
              disabled={loading || isSubmitting || items.length === 0}
            >
              <option value="">
                {loading ? "불러오는 중..." : "선택 안 함"}
              </option>
              {items.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.profileKey}
                  {item.targetJob ? ` (${getJobPositionLabel(item.targetJob)})` : " (공통)"}
                </option>
              ))}
            </select>
          </label>
        </div>

        {selectedPromptProfile ? (
          <div className="mt-4 rounded-2xl border border-[var(--line)] bg-white/70 px-4 py-3">
            <div className="text-sm font-semibold text-[var(--text)]">
              선택된 프롬프트 프로필
            </div>
            <div className="mt-1 text-sm text-[var(--text)]">
              {selectedPromptProfile.profileKey}
            </div>
            <div className="mt-1 text-xs text-[var(--muted)]">
              {selectedPromptProfile.targetJob
                ? `직무: ${getJobPositionLabel(selectedPromptProfile.targetJob)}`
                : "직무: 공통 프로필"}
            </div>
            <div className="mt-2 text-xs text-[var(--muted)]">
              {selectedPromptProfile.systemPromptPreview}
              {selectedPromptProfile.systemPromptPreview.length >= 120 ? "..." : ""}
            </div>
          </div>
        ) : null}

        {error ? (
          <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
            {error}
          </div>
        ) : null}

        <div className="mt-6 flex flex-col gap-3 border-t border-[var(--line)] pt-5 sm:flex-row sm:justify-end">
          <button
            type="button"
            className={`${buttonClassName} border-[var(--line)] bg-[var(--panel-strong)] text-[var(--text)] hover:bg-white/80`}
            onClick={onClose}
            disabled={isSubmitting}
          >
            취소
          </button>
          <button
            type="button"
            className={`${buttonClassName} border-transparent bg-[var(--primary)] text-white hover:opacity-90`}
            onClick={handleConfirm}
            disabled={isSubmitting || selectedCount === 0}
          >
            {isSubmitting ? "생성 중..." : "세션 생성"}
          </button>
        </div>
      </div>
    </div>
  );
}
