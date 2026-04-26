import { getJobPositionLabel } from "../../common/candidateJobPosition";
import { InterviewSessionAssembledPayloadView } from "./InterviewSessionAssembledPayloadView";
import { InterviewSessionQuestionGenerationView } from "./InterviewSessionQuestionGenerationView";
import type { InterviewSessionDetailResponse } from "../types";

interface InterviewSessionDetailModalProps {
  open: boolean;
  detail: InterviewSessionDetailResponse | null;
  isLoading: boolean;
  isSaving: boolean;
  onClose: () => void;
  onEdit: (sessionId: number) => void;
  onDelete: (sessionId: number, candidateName: string) => void;
  onTriggerQuestionGeneration: (sessionId: number) => void;
}

function formatDateTime(value: string) {
  return value.replace("T", " ").slice(0, 16);
}

export function InterviewSessionDetailModal({
  open,
  detail,
  isLoading,
  isSaving,
  onClose,
  onEdit,
  onDelete,
  onTriggerQuestionGeneration,
}: InterviewSessionDetailModalProps) {
  if (!open) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-[95] flex items-center justify-center bg-slate-950/45 p-4 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="max-h-[90vh] w-full max-w-6xl overflow-y-auto rounded-[32px] border border-white/70 bg-[var(--panel)] p-7 shadow-[var(--shadow)]"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex flex-col gap-4 border-b border-[var(--line)] pb-5 md:flex-row md:items-start md:justify-between">
          <div>
            <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
              interview session detail
            </div>
            <h2 className="mt-2 text-2xl font-bold text-[var(--text)]">
              {detail ? `${detail.candidateName} 조립 데이터` : "면접 세션 상세"}
            </h2>
            <p className="mt-2 text-sm text-[var(--muted)]">
              실제 `request_candidate_interview_prep(...)` 호출 직전 payload를 확인하는 모달입니다.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {detail ? (
              <>
                <button
                  type="button"
                  className="inline-flex h-10 items-center justify-center rounded-xl border border-rose-200 bg-rose-50 px-4 text-sm font-semibold text-rose-700 transition hover:bg-rose-100 disabled:cursor-not-allowed disabled:opacity-50"
                  onClick={() => onDelete(detail.id, detail.candidateName)}
                  disabled={isSaving}
                >
                  삭제
                </button>
              </>
            ) : null}
            <button
              type="button"
              className="inline-flex h-10 items-center justify-center rounded-xl border border-[var(--line)] bg-[var(--panel-strong)] px-4 text-sm font-semibold text-[var(--text)] transition hover:bg-white/80"
              onClick={onClose}
              disabled={isSaving}
            >
              닫기
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="py-12 text-center text-sm text-[var(--muted)]">
            상세 데이터를 불러오는 중입니다...
          </div>
        ) : null}

        {detail ? (
          <div className="mt-6 space-y-6">
            <section className="grid gap-4 md:grid-cols-4">
              <div className="rounded-[28px] border border-white/70 bg-[var(--panel-strong)] p-5">
                <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
                  Session ID
                </div>
                <div className="mt-3 text-lg font-bold text-[var(--text)]">{detail.id}</div>
              </div>
              <div className="rounded-[28px] border border-white/70 bg-[var(--panel-strong)] p-5">
                <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
                  목표 직무
                </div>
                <div className="mt-3 text-lg font-bold text-[var(--text)]">
                  {getJobPositionLabel(detail.targetJob)}
                </div>
              </div>
              <div className="rounded-[28px] border border-white/70 bg-[var(--panel-strong)] p-5">
                <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
                  난이도
                </div>
                <div className="mt-3 text-lg font-bold text-[var(--text)]">
                  {detail.difficultyLevel ?? "-"}
                </div>
              </div>
              <div className="rounded-[28px] border border-white/70 bg-[var(--panel-strong)] p-5">
                <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
                  생성 시각
                </div>
                <div className="mt-3 text-lg font-bold text-[var(--text)]">
                  {formatDateTime(detail.createdAt)}
                </div>
              </div>
            </section>

            <InterviewSessionQuestionGenerationView sessionId={detail.id} compact />

            <InterviewSessionAssembledPayloadView detail={detail} compact />
          </div>
        ) : null}
      </div>
    </div>
  );
}
