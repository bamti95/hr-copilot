import { CheckCircle2, LoaderCircle, RefreshCcw, UserRound, X } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { getErrorMessage } from "../../../../utils/getErrorMessage";
import { getJobPositionLabel } from "../../common/candidateJobPosition";
import { InterviewSessionQuestionGenerationView } from "./InterviewSessionQuestionGenerationView";
import { triggerInterviewQuestionGeneration } from "../services/interviewSessionService";
import type {
  InterviewSessionDetailResponse,
  InterviewSessionGraphPipeline,
} from "../types";

interface InterviewSessionDetailModalProps {
  open: boolean;
  detail: InterviewSessionDetailResponse | null;
  isLoading: boolean;
  isSaving: boolean;
  onClose: () => void;
  onDelete: (sessionId: number, candidateName: string) => void;
}

interface CandidateContext {
  name: string;
  targetJobLabel: string;
  jobPositionLabel: string;
  applyStatus: string;
  phone: string;
  difficulty: string;
}

function extractCandidateContext(detail: InterviewSessionDetailResponse): CandidateContext {
  const payload = detail.assembledPayloadPreview;

  return {
    name: payload.candidate.name,
    targetJobLabel: getJobPositionLabel(detail.targetJob),
    jobPositionLabel: payload.candidate.jobPosition
      ? getJobPositionLabel(payload.candidate.jobPosition)
      : "미입력",
    applyStatus: payload.candidate.applyStatus ?? "미입력",
    phone: payload.candidate.phone ?? "-",
    difficulty: detail.difficultyLevel ?? "미설정",
  };
}

function SummaryPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[24px] border border-slate-200 bg-white/80 px-4 py-4">
      <div className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--muted)]">
        {label}
      </div>
      <div className="mt-2 text-base font-bold text-[var(--text)]">{value}</div>
    </div>
  );
}

export function InterviewSessionDetailModal({
  open,
  detail,
  isLoading,
  isSaving,
  onClose,
  onDelete,
}: InterviewSessionDetailModalProps) {
  const [selectedQuestionIds, setSelectedQuestionIds] = useState<string[]>([]);
  const [regeneratingQuestionIds, setRegeneratingQuestionIds] = useState<string[]>([]);
  const [questionRefreshKey, setQuestionRefreshKey] = useState(0);
  const [isQuestionActionPending, setIsQuestionActionPending] = useState(false);
  const [isQuestionGenerationBusy, setIsQuestionGenerationBusy] = useState(false);
  const [questionActionError, setQuestionActionError] = useState("");
  const [graphPipeline, setGraphPipeline] =
    useState<InterviewSessionGraphPipeline>("default");
  const isQuestionRegenerationLocked =
    isQuestionActionPending || regeneratingQuestionIds.length > 0;

  const context = useMemo(() => {
    if (!detail) {
      return null;
    }
    return extractCandidateContext(detail);
  }, [detail]);

  useEffect(() => {
    if (!open) {
      setSelectedQuestionIds([]);
      setQuestionActionError("");
      setIsQuestionActionPending(false);
      setIsQuestionGenerationBusy(false);
      setRegeneratingQuestionIds([]);
    }
  }, [open]);

  useEffect(() => {
    setSelectedQuestionIds([]);
    setRegeneratingQuestionIds([]);
    setQuestionActionError("");
  }, [detail?.id]);

  const handleQuestionRegenerationComplete = useCallback(() => {
    setRegeneratingQuestionIds([]);
    setIsQuestionActionPending(false);
    setSelectedQuestionIds([]);
  }, []);

  if (!open) {
    return null;
  }

  const handleRegenerateQuestions = async () => {
    if (!detail || selectedQuestionIds.length === 0) {
      return;
    }

    try {
      setIsQuestionActionPending(true);
      setQuestionActionError("");
      setRegeneratingQuestionIds(selectedQuestionIds);
      await triggerInterviewQuestionGeneration(detail.id, {
        triggerType: "REGENERATE_SELECTED",
        targetQuestionIds: selectedQuestionIds,
        graphPipeline,
      });
      setSelectedQuestionIds([]);
      setQuestionRefreshKey((current) => current + 1);
    } catch (error) {
      setRegeneratingQuestionIds([]);
      setIsQuestionActionPending(false);
      setQuestionActionError(
        getErrorMessage(error, "선택한 질문 재생성 요청에 실패했습니다."),
      );
    }
  };

  const handleConfirmQuestions = () => {
    setSelectedQuestionIds([]);
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-[95] flex items-center justify-center overflow-hidden bg-slate-950/45 p-2 backdrop-blur-sm sm:p-4"
      onClick={() => {
        if (!isQuestionRegenerationLocked) {
          onClose();
        }
      }}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="flex h-[92dvh] max-h-[92dvh] w-full max-w-6xl min-w-0 flex-col overflow-hidden rounded-[24px] border border-white/70 bg-[var(--panel)] shadow-[0_40px_120px_rgba(15,23,42,0.25)] sm:rounded-[34px]"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex shrink-0 items-start justify-between gap-4 border-b border-[var(--line)] px-4 py-4 sm:px-7 sm:py-6">
          <div className="min-w-0">
            <div className="text-xs font-bold uppercase tracking-[0.16em] text-[var(--muted)]">
              Interview Session Brief
            </div>
            <h2 className="mt-2 truncate text-xl font-bold text-[var(--text)] sm:text-3xl">
              {detail ? `${detail.candidateName}님의 면접 세션` : "면접 세션"}
            </h2>
            <p className="mt-2 text-sm text-[var(--muted)]">
              생성된 면접 질문과 지원자 요약을 확인합니다.
            </p>
          </div>

          <button
            type="button"
            className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-[var(--line)] bg-white/80 text-slate-500 transition hover:bg-slate-50 hover:text-slate-900"
            onClick={onClose}
            aria-label="닫기"
            disabled={isSaving || isQuestionRegenerationLocked}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {isLoading ? (
          <div className="min-h-0 flex-1 overflow-y-auto px-4 py-16 text-center text-sm text-[var(--muted)] sm:px-7">
            세션 상세 정보를 불러오는 중입니다...
          </div>
        ) : null}

        {detail && context ? (
          <>
            <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
              <div className="grid gap-3 border-b border-[var(--line)] px-4 py-4 sm:px-7 sm:py-5 md:grid-cols-3">
                <SummaryPill label="세션" value={`#${detail.id}`} />
                <SummaryPill label="목표 직무" value={context.targetJobLabel} />
                <SummaryPill label="난이도" value={context.difficulty} />
              </div>

              <div className="border-b border-[var(--line)] px-4 py-5 sm:px-7">
                <div className="mb-3 flex items-center gap-3">
                  <div className="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-sky-100 text-sky-700">
                    <UserRound className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-[var(--text)]">지원자 요약</h3>
                    <p className="text-sm text-[var(--muted)]">
                      모달 상단에서 핵심 지원자 정보를 가로형으로 바로 확인합니다.
                    </p>
                  </div>
                </div>

                <div className="grid gap-3 md:grid-cols-4">
                  <SummaryPill label="이름" value={context.name} />
                  <SummaryPill label="지원 직무" value={context.jobPositionLabel} />
                  <SummaryPill label="지원 상태" value={context.applyStatus} />
                  <SummaryPill label="연락처" value={context.phone} />
                </div>
              </div>

              <InterviewSessionQuestionGenerationView
                sessionId={detail.id}
                compact
                selectable
                graphPipeline={graphPipeline}
                selectedQuestionIds={selectedQuestionIds}
                regeneratingQuestionIds={regeneratingQuestionIds}
                isRegenerationPending={isQuestionRegenerationLocked}
                refreshKey={questionRefreshKey}
                onBusyChange={setIsQuestionGenerationBusy}
                onRegenerationComplete={handleQuestionRegenerationComplete}
                onSelectedQuestionIdsChange={setSelectedQuestionIds}
              />

              {questionActionError ? (
                <div className="mx-4 mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700 sm:mx-7">
                  {questionActionError}
                </div>
              ) : null}
            </div>

            <div className="flex shrink-0 flex-wrap items-center justify-between gap-3 border-t border-[var(--line)] bg-[var(--panel)] px-4 py-4 sm:px-7 sm:py-5">
              <button
                type="button"
                className="inline-flex h-11 items-center justify-center rounded-2xl border border-rose-200 bg-rose-50 px-4 text-sm font-semibold text-rose-700 transition hover:bg-rose-100 disabled:cursor-not-allowed disabled:opacity-50"
                onClick={() => onDelete(detail.id, detail.candidateName)}
                disabled={isSaving || isQuestionRegenerationLocked}
              >
                세션 삭제
              </button>

              <div className="flex flex-wrap items-center gap-3">
                <select
                  className="h-11 rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] px-3 text-sm font-semibold text-[var(--text)] outline-none transition focus:border-[var(--primary)]"
                  value={graphPipeline}
                  onChange={(event) =>
                    setGraphPipeline(event.target.value as InterviewSessionGraphPipeline)
                  }
                  disabled={
                    isSaving ||
                    isQuestionRegenerationLocked ||
                    isQuestionGenerationBusy
                  }
                  aria-label="Graph pipeline"
                >
                  <option value="default">Default</option>
                  <option value="jh">JH</option>
                  <option value="hy">HY</option>
                  <option value="jy">JY</option>
                </select>
                <button
                  type="button"
                  className="inline-flex h-11 items-center justify-center gap-2 rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] px-5 text-sm font-semibold text-[var(--text)] transition hover:bg-white/80 disabled:cursor-not-allowed disabled:opacity-50"
                  onClick={() => void handleRegenerateQuestions()}
                  disabled={
                    isSaving ||
                    isQuestionRegenerationLocked ||
                    isQuestionGenerationBusy ||
                    selectedQuestionIds.length === 0
                  }
                >
                  {isQuestionRegenerationLocked ? (
                    <LoaderCircle className="h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCcw className="h-4 w-4" />
                  )}
                  {isQuestionRegenerationLocked ? "재생성 중" : "선택 질문 재생성"}
                </button>
                <button
                  type="button"
                  className="inline-flex h-11 items-center justify-center gap-2 rounded-2xl bg-linear-to-r from-[var(--primary)] to-[var(--primary-strong)] px-5 text-sm font-semibold text-white shadow-[0_18px_36px_color-mix(in_srgb,var(--primary)_24%,transparent)] transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-50"
                  onClick={handleConfirmQuestions}
                  disabled={isSaving || isQuestionRegenerationLocked}
                >
                  <CheckCircle2 className="h-4 w-4" />
                  질문 확정
                </button>
                <button
                  type="button"
                  className="inline-flex h-11 items-center justify-center rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] px-5 text-sm font-semibold text-[var(--text)] transition hover:bg-white/80 disabled:cursor-not-allowed disabled:opacity-50"
                  onClick={onClose}
                  disabled={isSaving || isQuestionRegenerationLocked}
                >
                  닫기
                </button>
              </div>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
