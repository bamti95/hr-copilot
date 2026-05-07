import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  LoaderCircle,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { getErrorMessage } from "../../../../utils/getErrorMessage";
import {
  fetchInterviewQuestionGenerationStatus,
  triggerInterviewQuestionGeneration,
} from "../services/interviewSessionService";
import type {
  InterviewGeneratedQuestion,
  InterviewQuestionGenerationStatus,
  InterviewQuestionGenerationProgressStep,
  InterviewQuestionReviewStatus,
  InterviewQuestionGenerationStatusResponse,
} from "../types";

import { formatDateTime } from "../../common/formatDateTime";


interface InterviewSessionQuestionGenerationViewProps {
  sessionId: number;
  compact?: boolean;
  selectable?: boolean;
  selectedQuestionIds?: string[];
  refreshKey?: number;
  onBusyChange?: (isBusy: boolean) => void;
  onSelectedQuestionIdsChange?: (questionIds: string[]) => void;
}

const RUNNING_STATUSES = new Set<InterviewQuestionGenerationStatus>([
  "QUEUED",
  "PROCESSING",
]);
const SUCCESS_STATUSES = new Set<InterviewQuestionGenerationStatus>([
  "COMPLETED",
  "PARTIAL_COMPLETED",
]);

function getGenerationStatusStyle(status: InterviewQuestionGenerationStatus) {
  if (status === "COMPLETED") {
    return "border-emerald-200 bg-emerald-50 text-emerald-800";
  }
  if (status === "PARTIAL_COMPLETED") {
    return "border-amber-200 bg-amber-50 text-amber-800";
  }
  if (status === "FAILED") {
    return "border-rose-200 bg-rose-50 text-rose-700";
  }
  if (RUNNING_STATUSES.has(status)) {
    return "border-sky-200 bg-sky-50 text-sky-800";
  }
  return "border-slate-200 bg-slate-50 text-slate-700";
}

function getGenerationStatusLabel(status: InterviewQuestionGenerationStatus) {
  const labels: Record<InterviewQuestionGenerationStatus, string> = {
    NOT_REQUESTED: "생성 전",
    QUEUED: "생성 대기 중",
    PROCESSING: "생성 중",
    COMPLETED: "생성 완료",
    PARTIAL_COMPLETED: "일부 완료",
    FAILED: "생성 실패",
  };
  return labels[status] ?? status;
}

function getGenerationStatusMessage(status: InterviewQuestionGenerationStatus) {
  if (status === "QUEUED") {
    return "질문 생성 작업이 대기열에 등록되었습니다. 곧 생성이 시작됩니다.";
  }
  if (status === "PROCESSING") {
    return "질문 생성이 진행 중입니다. 완료되면 결과가 자동으로 갱신됩니다.";
  }
  if (status === "COMPLETED") {
    return "질문 생성이 완료되었습니다.";
  }
  if (status === "PARTIAL_COMPLETED") {
    return "질문 일부가 생성되었습니다. 실패한 항목은 오류 내용을 확인해 주세요.";
  }
  if (status === "FAILED") {
    return "질문 생성에 실패했습니다. 오류 내용을 확인한 뒤 다시 생성할 수 있습니다.";
  }
  return "아직 질문 생성 작업이 요청되지 않았습니다.";
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

function getNodeStatusLabel(status: InterviewQuestionGenerationProgressStep["status"]) {
  const labels: Record<InterviewQuestionGenerationProgressStep["status"], string> = {
    PENDING: "대기",
    PROCESSING: "진행 중",
    COMPLETED: "완료",
    FAILED: "실패",
  };
  return labels[status];
}

function getNodeStatusStyle(status: InterviewQuestionGenerationProgressStep["status"]) {
  if (status === "COMPLETED") {
    return "border-emerald-200 bg-emerald-50 text-emerald-800";
  }
  if (status === "PROCESSING") {
    return "border-sky-200 bg-sky-50 text-sky-800";
  }
  if (status === "FAILED") {
    return "border-rose-200 bg-rose-50 text-rose-700";
  }
  return "border-slate-200 bg-slate-50 text-slate-600";
}

function NodeStatusIcon({
  status,
}: {
  status: InterviewQuestionGenerationProgressStep["status"];
}) {
  if (status === "PROCESSING") {
    return <LoaderCircle className="h-4 w-4 animate-spin" />;
  }
  if (status === "COMPLETED") {
    return <CheckCircle2 className="h-4 w-4" />;
  }
  if (status === "FAILED") {
    return <AlertTriangle className="h-4 w-4" />;
  }
  return <span className="h-2.5 w-2.5 rounded-full bg-slate-300" />;
}

function truncateText(value: string, maxLength = 320) {
  const text = value.trim();
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, maxLength - 1).trim()}…`;
}

interface QuestionCardProps {
  question: InterviewGeneratedQuestion;
  index: number;
  selectable?: boolean;
  isSelected?: boolean;
  selectionDisabled?: boolean;
  onToggleSelection?: (questionId: string) => void;
}

function QuestionCard({
  question,
  index,
  selectable = false,
  isSelected = false,
  selectionDisabled = false,
  onToggleSelection,
}: QuestionCardProps) {
  const checkboxId = `question-select-${question.id}`;

  return (
    <article className="min-w-0 rounded-2xl border border-[var(--line)] bg-white/85 p-4 sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          {selectable ? (
            <label
              className="inline-flex h-8 w-8 cursor-pointer items-center justify-center rounded-lg border border-slate-300 bg-white text-slate-700 transition hover:border-slate-400"
              htmlFor={checkboxId}
              title="재생성할 질문 선택"
            >
              <input
                id={checkboxId}
                type="checkbox"
                className="h-4 w-4 accent-[var(--primary)]"
                checked={isSelected}
                disabled={selectionDisabled}
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
            {question.predictedAnswer ? truncateText(question.predictedAnswer) : "-"}
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

      <details className="mt-4 rounded-xl border border-[var(--line)] bg-white/70 p-4">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-sm font-bold text-[var(--text)]">
          근거와 평가 가이드
          <ChevronDown className="h-4 w-4 text-[var(--muted)]" />
        </summary>
        <div className="mt-4 grid gap-3 break-words text-sm leading-6 text-[var(--text)] [overflow-wrap:anywhere]">
          <div>
            <div className="font-bold">질문 생성 근거</div>
            <p className="mt-1 text-[var(--muted)]">{question.generationBasis || "-"}</p>
          </div>
          <div>
            <div className="font-bold">문서 근거</div>
            {question.documentEvidence.length > 0 ? (
              <ul className="mt-1 space-y-1 text-[var(--muted)]">
                {question.documentEvidence.map((evidence, evidenceIndex) => (
                  <li key={`${question.id}-evidence-${evidenceIndex}`}>{evidence}</li>
                ))}
              </ul>
            ) : (
              <p className="mt-1 text-[var(--muted)]">-</p>
            )}
          </div>
          <div>
            <div className="font-bold">평가 가이드</div>
            <p className="mt-1 text-[var(--muted)]">{question.evaluationGuide || "-"}</p>
          </div>
          <div>
            <div className="font-bold">리뷰 / 점수 근거</div>
            <p className="mt-1 text-[var(--muted)]">
              {question.review.reason || "-"} / {question.scoreReason || "-"}
            </p>
          </div>
        </div>
      </details>

    </article>
  );
}

export function InterviewSessionQuestionGenerationView({
  sessionId,
  compact = false,
  selectable = false,
  selectedQuestionIds = [],
  refreshKey = 0,
  onBusyChange,
  onSelectedQuestionIdsChange,
}: InterviewSessionQuestionGenerationViewProps) {
  const [data, setData] = useState<InterviewQuestionGenerationStatusResponse | null>(
    null,
  );
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isTriggering, setIsTriggering] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const isRunning = data ? RUNNING_STATUSES.has(data.status) : false;
  const generationProgress = useMemo(() => {
    const status = data?.status ?? "NOT_REQUESTED";
    const completed = SUCCESS_STATUSES.has(status) ? 1 : 0;
    const running = RUNNING_STATUSES.has(status) ? 1 : 0;
    const failed = status === "FAILED" ? 1 : 0;

    return {
      completed,
      running,
      failed,
      total: status === "NOT_REQUESTED" ? 0 : 1,
    };
  }, [data?.status]);

  const loadStatus = useCallback(
    async (options?: { quiet?: boolean }) => {
      try {
        if (options?.quiet) {
          setIsRefreshing(true);
        } else {
          setIsLoading(true);
        }
        setErrorMessage("");
        const response = await fetchInterviewQuestionGenerationStatus(sessionId);
        setData(response);
      } catch (error) {
        // 401: refresh token 갱신까지 실패한 인증 만료 상태.
        // data를 null로 리셋해 isRunning=false로 만들어 폴링 인터벌이 즉시
        // 정리되도록 한다(useEffect cleanup이 동작). axios 인터셉터가 이미
        // auth:unauthorized 이벤트를 발생시켜 전역 로그아웃 처리를 진행하므로,
        // 여기서는 화면 안내와 폴링 중단만 담당한다.
        const status = (error as { response?: { status?: number } })?.response?.status;
        if (status === 401) {
          setData(null);
          setErrorMessage("로그인이 만료되었습니다. 다시 로그인해 주세요.");
          return;
        }
        setErrorMessage(
          getErrorMessage(error, "질문 생성 결과를 불러오지 못했습니다."),
        );
      } finally {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    },
    [sessionId],
  );

  useEffect(() => {
    void loadStatus();
  }, [loadStatus, refreshKey]);

  useEffect(() => {
    if (!isRunning) {
      return;
    }
    const timer = window.setInterval(() => {
      void loadStatus({ quiet: true });
    }, 3000);
    return () => window.clearInterval(timer);
  }, [isRunning, loadStatus]);

  const handleTriggerGeneration = async () => {
    try {
      setIsTriggering(true);
      setErrorMessage("");
      await triggerInterviewQuestionGeneration(sessionId, { triggerType: "MANUAL" });
      onSelectedQuestionIdsChange?.([]);
      await loadStatus({ quiet: true });
    } catch (error) {
      setErrorMessage(
        getErrorMessage(error, "질문 생성 작업을 등록하지 못했습니다."),
      );
    } finally {
      setIsTriggering(false);
    }
  };

  useEffect(() => {
    onBusyChange?.(isLoading || isRefreshing || isTriggering || isRunning);
  }, [isLoading, isRefreshing, isTriggering, isRunning, onBusyChange]);

  const handleToggleQuestionSelection = (questionId: string) => {
    if (!onSelectedQuestionIdsChange) {
      return;
    }

    onSelectedQuestionIdsChange(
      selectedQuestionIds.includes(questionId)
        ? selectedQuestionIds.filter((id) => id !== questionId)
        : [...selectedQuestionIds, questionId],
    );
  };

  const statusSummary = useMemo(() => {
    const questions = data?.questions ?? [];
    return {
      approved: questions.filter((question) => question.review.status === "approved").length,
      needsRevision: questions.filter(
        (question) => question.review.status === "needs_revision",
      ).length,
      rejected: questions.filter((question) => question.review.status === "rejected").length,
    };
  }, [data]);
  const visibleProgress = useMemo(
    () =>
      (data?.progress ?? []).filter(
        (step) =>
          !step.key.startsWith("retry_") ||
          step.status !== "PENDING" ||
          step.attempt > 0,
      ),
    [data?.progress],
  );

  return (
    <section
      className={
        compact
          ? "min-w-0 border-b border-[var(--line)] bg-white/45 px-4 py-5 sm:px-7"
          : "min-w-0 rounded-[32px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)] sm:p-7"
      }
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex rounded-full border border-cyan-200 bg-cyan-50 px-3 py-1 text-xs font-bold uppercase tracking-[0.12em] text-cyan-800">
              LangGraph Result
            </span>
            {data ? (
              <span
                className={`inline-flex rounded-full border px-3 py-1 text-xs font-bold ${getGenerationStatusStyle(
                  data.status,
                )}`}
              >
                {getGenerationStatusLabel(data.status)}
              </span>
            ) : null}
          </div>
          <h2 className="mt-3 text-xl font-bold text-[var(--text)] sm:text-2xl">
            생성된 면접 질문
          </h2>
          <p className="mt-2 break-words text-sm leading-6 text-[var(--muted)] [overflow-wrap:anywhere]">
            LangGraph 멀티 에이전트가 만든 질문, 예상 답변, 꼬리 질문, 근거와 점수를 확인합니다.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="inline-flex h-10 items-center gap-2 rounded-xl border border-[var(--line)] bg-[var(--panel-strong)] px-4 text-sm font-bold text-[var(--text)] transition hover:bg-white/80 disabled:cursor-not-allowed disabled:opacity-50"
            onClick={() => void loadStatus({ quiet: true })}
            disabled={isRefreshing || isLoading}
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
            새로고침
          </button>
          <button
            type="button"
            className="inline-flex h-10 items-center gap-2 rounded-xl bg-slate-950 px-4 text-sm font-bold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            onClick={() => void handleTriggerGeneration()}
            disabled={isTriggering || isRunning}
          >
            {isTriggering || isRunning ? (
              <LoaderCircle className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            전체 재생성
          </button>
        </div>
      </div>

      {isRunning ? (
        <div className="mt-5 inline-flex max-w-full items-center gap-2 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-700">
          <LoaderCircle className="h-4 w-4 animate-spin" />
          <span className="break-words [overflow-wrap:anywhere]">
            {getGenerationStatusMessage(data.status)}
          </span>
          {isRefreshing ? <span>· 상태 확인 중</span> : null}
        </div>
      ) : null}

      {errorMessage ? (
        <div className="mt-5 flex items-start gap-2 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span className="break-words [overflow-wrap:anywhere]">{errorMessage}</span>
        </div>
      ) : null}

      {data ? (
        <div className="mt-5 grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-600 md:grid-cols-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
              완료
            </p>
            <p className="mt-1 text-base font-semibold text-slate-900">
              {generationProgress.completed} / {generationProgress.total}
            </p>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
              생성 중
            </p>
            <p className="mt-1 text-base font-semibold text-amber-600">
              {generationProgress.running}
            </p>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
              실패
            </p>
            <p className="mt-1 text-base font-semibold text-rose-600">
              {generationProgress.failed}
            </p>
          </div>
        </div>
      ) : null}

      {data ? (
        <div className="mt-5 rounded-2xl border border-slate-200 bg-white p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-sm font-semibold text-slate-900">
                면접 질문 생성 작업
              </p>
              <p className="mt-1 break-words text-xs text-slate-500 [overflow-wrap:anywhere]">
                요청 {formatDateTime(data.requestedAt)} / 완료{" "}
                {formatDateTime(data.completedAt)}
              </p>
            </div>
            <span
              className={`inline-flex min-w-[104px] items-center justify-center rounded-full border px-3 py-2 text-xs font-bold ${getGenerationStatusStyle(
                data.status,
              )}`}
            >
              {getGenerationStatusLabel(data.status)}
            </span>
          </div>

          {isRunning ? (
            <div className="mt-4 inline-flex max-w-full items-center gap-2 rounded-xl bg-amber-50 px-3 py-2 text-xs font-medium text-amber-700">
              <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
              <span>생성 처리 중입니다. 완료되면 질문 목록이 자동으로 갱신됩니다.</span>
            </div>
          ) : (
            <p className="mt-4 break-words text-xs font-medium text-slate-500 [overflow-wrap:anywhere]">
              {getGenerationStatusMessage(data.status)}
            </p>
          )}
        </div>
      ) : null}

      {visibleProgress.length ? (
        <div className="mt-5 rounded-2xl border border-slate-200 bg-white p-4">
          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-semibold text-slate-900">
                LangGraph 노드 진행 상태
              </p>
              <p className="mt-1 break-words text-xs text-slate-500 [overflow-wrap:anywhere]">
                생성 작업이 각 에이전트 노드를 통과한 상태입니다.
              </p>
            </div>
            <span className="text-xs font-semibold text-slate-500">
              {visibleProgress.filter((step) => step.status === "COMPLETED").length} /{" "}
              {visibleProgress.length}
            </span>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {visibleProgress.map((step) => (
              <div
                key={step.key}
                className={`rounded-2xl border px-4 py-3 ${getNodeStatusStyle(
                  step.status,
                )}`}
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex min-w-0 items-center gap-2">
                    <NodeStatusIcon status={step.status} />
                    <span className="truncate text-sm font-bold">{step.label}</span>
                  </div>
                  <span className="shrink-0 text-xs font-bold">
                    {getNodeStatusLabel(step.status)}
                  </span>
                </div>
                <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 break-words text-xs opacity-80 [overflow-wrap:anywhere]">
                  <span>시작 {formatDateTime(step.startedAt)}</span>
                  <span>완료 {formatDateTime(step.completedAt)}</span>
                  {step.attempt > 1 ? <span>{step.attempt}회 실행</span> : null}
                </div>
                {step.error ? (
                  <p className="mt-2 text-xs font-medium text-rose-700">{step.error}</p>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <div className="mt-5 grid gap-3 md:grid-cols-5">
        <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] p-4">
          <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
            Questions
          </div>
          <div className="mt-2 text-xl font-bold text-[var(--text)]">
            {data?.questions.length ?? 0}
          </div>
        </div>
        <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] p-4">
          <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
            승인
          </div>
          <div className="mt-2 text-xl font-bold text-emerald-700">
            {statusSummary.approved}
          </div>
        </div>
        <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] p-4">
          <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
            수정 필요
          </div>
          <div className="mt-2 text-xl font-bold text-amber-600">
            {statusSummary.needsRevision}
          </div>
        </div>
        <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] p-4">
          <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
            반려
          </div>
          <div className="mt-2 text-xl font-bold text-rose-700">
            {statusSummary.rejected}
          </div>
        </div>
        <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] p-4">
          <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
            세션 완료 시각
          </div>
          <div className="mt-2 text-sm font-bold text-[var(--text)]">
            {formatDateTime(data?.completedAt ?? null)}
          </div>
        </div>
      </div>

      {data?.generationSource ? (
        <details className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-sm font-bold text-slate-800">
            백엔드 생성 함수 추적
            <ChevronDown className="h-4 w-4 text-slate-500" />
          </summary>
          <dl className="mt-4 grid gap-2 text-xs leading-5 text-slate-700">
            {Object.entries(data.generationSource).map(([key, value]) => (
              <div key={key} className="grid gap-1 md:grid-cols-[160px_1fr]">
                <dt className="font-bold uppercase tracking-[0.08em] text-slate-500">
                  {key}
                </dt>
                <dd className="break-words font-mono">{value}</dd>
              </div>
            ))}
          </dl>
        </details>
      ) : null}

      {data?.error ? (
        <div className="mt-5 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          {data.error}
        </div>
      ) : null}

      {isLoading ? (
        <div className="mt-6 flex items-center gap-2 rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] p-5 text-sm text-[var(--muted)]">
          <LoaderCircle className="h-4 w-4 animate-spin" />
          질문 생성 결과를 불러오는 중입니다.
        </div>
      ) : null}

      {!isLoading && data && data.questions.length === 0 ? (
        <div className="mt-6 rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] p-6 text-sm leading-6 text-[var(--muted)]">
          아직 저장된 질문이 없습니다. 상태가 생성 중이면 잠시 후 자동으로 갱신되고,
          실패 상태라면 전체 재생성으로 다시 요청할 수 있습니다.
        </div>
      ) : null}

      {!isLoading && data && data.questions.length > 0 ? (
        <div className={`mt-6 grid gap-4 ${compact ? "" : "xl:grid-cols-2"}`}>
          {data.questions.map((question, index) => (
            <QuestionCard
              key={question.id}
              question={question}
              index={index}
              selectable={selectable}
              isSelected={selectedQuestionIds.includes(question.id)}
              selectionDisabled={isRunning || isTriggering}
              onToggleSelection={handleToggleQuestionSelection}
            />
          ))}
        </div>
      ) : null}

      {!compact ? (
        <div className="mt-5 flex items-center gap-2 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          질문을 체크한 뒤 하단의 질문 재생성 버튼으로 선택 항목을 다시 생성할 수 있습니다.
        </div>
      ) : null}
    </section>
  );
}
