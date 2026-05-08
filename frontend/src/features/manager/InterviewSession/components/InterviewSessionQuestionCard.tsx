import { ChevronDown, LoaderCircle } from "lucide-react";
import type {
  InterviewGeneratedQuestion,
  InterviewQuestionReviewStatus,
} from "../types";

interface InterviewSessionQuestionCardProps {
  question: InterviewGeneratedQuestion;
  index: number;
  selectable?: boolean;
  isSelected?: boolean;
  selectionDisabled?: boolean;
  isRegenerating?: boolean;
  interactionDisabled?: boolean;
  onToggleSelection?: (questionId: string) => void;
}

function getReviewStatusLabel(status: InterviewQuestionReviewStatus) {
  const labels: Record<InterviewQuestionReviewStatus, string> = {
    approved: "승인",
    needs_revision: "수정 필요",
    rejected: "반려",
  };
  return labels[status];
}

function getReviewStatusStyle(status: InterviewQuestionReviewStatus) {
  if (status === "approved") {
    return "bg-emerald-50 text-emerald-700";
  }
  if (status === "needs_revision") {
    return "bg-amber-50 text-amber-700";
  }
  return "bg-rose-50 text-rose-700";
}

function truncateText(value: string, maxLength = 320) {
  const text = value.trim();
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, maxLength - 1).trim()}...`;
}

export function InterviewSessionQuestionCard({
  question,
  index,
  selectable = false,
  isSelected = false,
  selectionDisabled = false,
  isRegenerating = false,
  interactionDisabled = false,
  onToggleSelection,
}: InterviewSessionQuestionCardProps) {
  const checkboxId = `question-select-${question.id}`;
  const isSelectionDisabled = selectionDisabled || isRegenerating || interactionDisabled;

  return (
    <article
      className={`relative min-w-0 overflow-hidden rounded-2xl border bg-white/85 p-4 transition sm:p-5 ${
        isRegenerating
          ? "border-sky-300 shadow-[0_18px_42px_rgba(14,165,233,0.14)]"
          : "border-[var(--line)]"
      }`}
      aria-busy={isRegenerating}
    >
      {isRegenerating ? (
        <div className="pointer-events-none absolute inset-x-0 top-0 h-1 overflow-hidden bg-sky-100">
          <div className="h-full w-1/2 animate-pulse rounded-full bg-sky-500" />
        </div>
      ) : null}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          {selectable ? (
            <label
              className="inline-flex h-8 w-8 cursor-pointer items-center justify-center rounded-lg border border-slate-300 bg-white text-slate-700 transition hover:border-slate-400 has-[:disabled]:cursor-not-allowed has-[:disabled]:opacity-60"
              htmlFor={checkboxId}
              title="재생성할 질문 선택"
            >
              <input
                id={checkboxId}
                type="checkbox"
                className="h-4 w-4 accent-[var(--primary)]"
                checked={isSelected}
                disabled={isSelectionDisabled}
                onChange={() => onToggleSelection?.(question.id)}
                aria-label={`Q${index + 1} 재생성 대상 선택`}
              />
            </label>
          ) : null}
          <span className="inline-flex rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">
            Q{index + 1}
          </span>
          <span className="inline-flex rounded-full bg-cyan-50 px-3 py-1 text-xs font-bold text-cyan-800">
            {question.category}
          </span>
          <span
            className={`inline-flex rounded-full px-3 py-1 text-xs font-bold ${getReviewStatusStyle(
              question.review.status,
            )}`}
          >
            {getReviewStatusLabel(question.review.status)}
          </span>
          {isRegenerating ? (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-sky-50 px-3 py-1 text-xs font-bold text-sky-700">
              <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
              재생성 중
            </span>
          ) : null}
        </div>
        <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-bold text-slate-700">
          score {question.score}
        </div>
      </div>

      <h3 className="mt-4 break-words text-base font-bold leading-7 text-[var(--text)] [overflow-wrap:anywhere] sm:text-lg">
        {question.questionText}
      </h3>

      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        <div className="rounded-xl border border-[var(--line)] bg-[var(--panel-strong)] p-4">
          <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
            예상 답변
          </div>
          <p className="mt-2 break-words text-sm leading-6 text-[var(--text)] [overflow-wrap:anywhere]">
            {question.predictedAnswer
              ? truncateText(question.predictedAnswer)
              : "-"}
          </p>
        </div>
        <div className="rounded-xl border border-[var(--line)] bg-[var(--panel-strong)] p-4">
          <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
            꼬리 질문
          </div>
          <p className="mt-2 break-words text-sm leading-6 text-[var(--text)] [overflow-wrap:anywhere]">
            {question.followUpQuestion || "-"}
          </p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {question.riskTags.map((tag) => (
          <span
            key={`risk-${question.id}-${tag}`}
            className="rounded-full bg-rose-50 px-3 py-1 text-xs font-semibold text-rose-700"
          >
            {tag}
          </span>
        ))}
        {question.competencyTags.map((tag) => (
          <span
            key={`competency-${question.id}-${tag}`}
            className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700"
          >
            {tag}
          </span>
        ))}
      </div>

      <details
        className={`mt-4 rounded-xl border border-[var(--line)] bg-white/70 p-4 ${
          interactionDisabled ? "pointer-events-none opacity-70" : ""
        }`}
      >
        <summary
          className={`flex list-none items-center justify-between gap-3 text-sm font-bold text-[var(--text)] ${
            interactionDisabled ? "cursor-not-allowed" : "cursor-pointer"
          }`}
        >
          근거와 평가 가이드
          <ChevronDown className="h-4 w-4 text-[var(--muted)]" />
        </summary>
        <div className="mt-4 grid gap-3 break-words text-sm leading-6 text-[var(--text)] [overflow-wrap:anywhere]">
          <div>
            <div className="font-bold">질문 생성 근거</div>
            <p className="mt-1 text-[var(--muted)]">
              {question.generationBasis || "-"}
            </p>
          </div>
          <div>
            <div className="font-bold">문서 근거</div>
            {question.documentEvidence.length > 0 ? (
              <ul className="mt-1 space-y-1 text-[var(--muted)]">
                {question.documentEvidence.map((evidence, evidenceIndex) => (
                  <li key={`${question.id}-evidence-${evidenceIndex}`}>
                    {evidence}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-1 text-[var(--muted)]">-</p>
            )}
          </div>
          <div>
            <div className="font-bold">평가 가이드</div>
            <p className="mt-1 text-[var(--muted)]">
              {question.evaluationGuide || "-"}
            </p>
          </div>
          <div>
            <div className="font-bold">리뷰 / 점수 근거</div>
            <p className="mt-1 text-[var(--muted)]">
              {question.review.reason || "-"} / {question.scoreReason || "-"}
            </p>
          </div>
        </div>
      </details>

      {isRegenerating ? (
        <div className="pointer-events-auto absolute inset-0 flex cursor-wait items-end justify-end bg-white/35 p-4">
          <div className="inline-flex items-center gap-2 rounded-xl border border-sky-200 bg-white/95 px-3 py-2 text-xs font-bold text-sky-700 shadow-sm">
            <LoaderCircle className="h-3.5 w-3.5 animate-spin" />새 질문으로
            교체 준비 중
          </div>
        </div>
      ) : null}
    </article>
  );
}
