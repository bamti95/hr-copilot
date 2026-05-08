import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
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
  InterviewSessionGraphPipeline,
  InterviewQuestionGenerationStatus,
  InterviewQuestionGenerationStatusResponse,
} from "../types";

import { formatDateTime } from "../../common/formatDateTime";
import { InterviewSessionQuestionCard } from "./InterviewSessionQuestionCard";

interface InterviewSessionQuestionGenerationViewProps {
  sessionId: number;
  compact?: boolean;
  selectable?: boolean;
  graphPipeline?: InterviewSessionGraphPipeline;
  selectedQuestionIds?: string[];
  regeneratingQuestionIds?: string[];
  isRegenerationPending?: boolean;
  refreshKey?: number;
  onBusyChange?: (isBusy: boolean) => void;
  onRegenerationComplete?: () => void;
  onSelectedQuestionIdsChange?: (questionIds: string[]) => void;
}

const RUNNING_STATUSES = new Set<InterviewQuestionGenerationStatus>([
  "QUEUED",
  "PROCESSING",
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
    QUEUED: "요청 접수",
    PROCESSING: "생성 중",
    COMPLETED: "생성 완료",
    PARTIAL_COMPLETED: "확인 필요",
    FAILED: "생성 실패",
  };
  return labels[status] ?? status;
}

function getGenerationStatusMessage(status: InterviewQuestionGenerationStatus) {
  if (status === "QUEUED") {
    return "면접 질문 생성 요청이 접수되었습니다. 잠시 후 자동으로 생성이 시작됩니다.";
  }
  if (status === "PROCESSING") {
    return "지원자 자료를 바탕으로 면접 질문을 생성하고 있습니다. 완료되면 결과가 자동으로 갱신됩니다.";
  }
  if (status === "COMPLETED") {
    return "면접 질문 생성이 완료되었습니다.";
  }
  if (status === "PARTIAL_COMPLETED") {
    return "일부 질문은 생성되었지만 검토가 필요합니다. 아래 결과를 확인해 주세요.";
  }
  if (status === "FAILED") {
    return "면접 질문 생성에 실패했습니다. 오류 내용을 확인한 뒤 다시 생성할 수 있습니다.";
  }
  return "아직 면접 질문 생성 요청 전입니다.";
}

export function InterviewSessionQuestionGenerationView({
  sessionId,
  compact = false,
  selectable = false,
  graphPipeline = "default",
  selectedQuestionIds = [],
  regeneratingQuestionIds = [],
  isRegenerationPending = false,
  refreshKey = 0,
  onBusyChange,
  onRegenerationComplete,
  onSelectedQuestionIdsChange,
}: InterviewSessionQuestionGenerationViewProps) {
  const [data, setData] = useState<InterviewQuestionGenerationStatusResponse | null>(
    null,
  );
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isTriggering, setIsTriggering] = useState(false);
  const [hasObservedRegenerationRunning, setHasObservedRegenerationRunning] =
    useState(false);
  const [regenerationBaseline, setRegenerationBaseline] = useState<{
    requestedAt: string | null;
    completedAt: string | null;
  } | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  const isRunning = data ? RUNNING_STATUSES.has(data.status) : false;
  const regeneratingQuestionIdSet = useMemo(
    () => new Set(regeneratingQuestionIds),
    [regeneratingQuestionIds],
  );
  const hasTargetedRegeneration = regeneratingQuestionIds.length > 0;
  const isRegenerationTracking =
    isRegenerationPending || hasTargetedRegeneration;
  const areQuestionActionsDisabled =
    isRunning || isTriggering || isRegenerationTracking;
  const showFullRegenerateButton =
    !compact ||
    !data ||
    data.status === "NOT_REQUESTED" ||
    data.status === "FAILED" ||
    data.questions.length === 0;
  const generationOverview = useMemo(() => {
    const status = data?.status ?? "NOT_REQUESTED";
    const questionCount = data?.questions.length ?? 0;
    const approvedCount =
      data?.questions.filter((question) => question.review.status === "approved")
        .length ?? 0;

    return [
      {
        label: "진행 상태",
        value: getGenerationStatusLabel(status),
        tone:
          status === "FAILED"
            ? "text-rose-600"
            : status === "PARTIAL_COMPLETED"
              ? "text-amber-600"
              : RUNNING_STATUSES.has(status)
                ? "text-sky-700"
                : "text-slate-900",
      },
      {
        label: "생성된 질문",
        value: `${questionCount}개`,
        tone: "text-slate-900",
      },
      {
        label: "승인된 질문",
        value: `${approvedCount}개`,
        tone: "text-emerald-700",
      },
      {
        label: "완료 시각",
        value: formatDateTime(data?.completedAt ?? null),
        tone: "text-slate-900",
      },
    ];
  }, [data]);

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
    if (!isRunning && !isRegenerationTracking) {
      return;
    }
    const timer = window.setInterval(() => {
      void loadStatus({ quiet: true });
    }, 3000);
    return () => window.clearInterval(timer);
  }, [isRunning, isRegenerationTracking, loadStatus]);

  useEffect(() => {
    if (!isRegenerationTracking) {
      setHasObservedRegenerationRunning(false);
      setRegenerationBaseline(null);
      return;
    }

    setRegenerationBaseline((current) =>
      current ??
      (data
        ? {
            requestedAt: data.requestedAt,
            completedAt: data.completedAt,
          }
        : null),
    );
  }, [data, isRegenerationTracking]);

  useEffect(() => {
    if (!isRegenerationTracking) {
      return;
    }

    if (isRunning) {
      setHasObservedRegenerationRunning(true);
    }
  }, [isRegenerationTracking, isRunning]);

  useEffect(() => {
    if (!isRegenerationTracking || !data || isRunning) {
      return;
    }

    const hasNewCompletedResult =
      regenerationBaseline !== null &&
      data.completedAt !== regenerationBaseline.completedAt;

    if (hasObservedRegenerationRunning || hasNewCompletedResult) {
      onRegenerationComplete?.();
    }
  }, [
    data,
    hasObservedRegenerationRunning,
    isRegenerationTracking,
    isRunning,
    onRegenerationComplete,
    regenerationBaseline,
  ]);

  const handleTriggerGeneration = async () => {
    try {
      setIsTriggering(true);
      setErrorMessage("");
      await triggerInterviewQuestionGeneration(sessionId, {
        triggerType: "MANUAL",
        graphPipeline,
      });
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
    onBusyChange?.(
      isLoading ||
        isRefreshing ||
        isTriggering ||
        isRunning ||
        isRegenerationTracking,
    );
  }, [
    isLoading,
    isRefreshing,
    isTriggering,
    isRunning,
    isRegenerationTracking,
    onBusyChange,
  ]);

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

  const isQuestionRegenerating = (questionId: string) => {
    if (!isRunning && !isTriggering && !isRegenerationPending) {
      return false;
    }

    if (hasTargetedRegeneration) {
      return regeneratingQuestionIdSet.has(questionId);
    }

    return isRunning || isTriggering;
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
              면접 질문
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
            지원자 자료를 바탕으로 생성된 질문과 예상 답변, 꼬리 질문, 검토 결과를 확인합니다.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="inline-flex h-10 items-center gap-2 rounded-xl border border-[var(--line)] bg-[var(--panel-strong)] px-4 text-sm font-bold text-[var(--text)] transition hover:bg-white/80 disabled:cursor-not-allowed disabled:opacity-50"
            onClick={() => void loadStatus({ quiet: true })}
            disabled={areQuestionActionsDisabled || isRefreshing || isLoading}
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
            새로고침
          </button>
          {showFullRegenerateButton ? (
            <button
              type="button"
              className="inline-flex h-10 items-center gap-2 rounded-xl bg-slate-950 px-4 text-sm font-bold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
              onClick={() => void handleTriggerGeneration()}
              disabled={areQuestionActionsDisabled}
            >
              {isTriggering || isRunning ? (
                <LoaderCircle className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              전체 재생성
            </button>
          ) : null}
        </div>
      </div>

      {isRunning ? (
        <div className="mt-5 inline-flex max-w-full items-center gap-2 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-700">
          <LoaderCircle className="h-4 w-4 animate-spin" />
          <span className="break-words [overflow-wrap:anywhere]">
            {getGenerationStatusMessage(data?.status ?? "NOT_REQUESTED")}
          </span>
          {isRefreshing ? <span>· 상태 확인 중</span> : null}
        </div>
      ) : null}

      {(isRunning || isTriggering || isRegenerationTracking) && data?.questions.length ? (
        <div className="mt-5 flex items-start gap-3 rounded-2xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-800">
          <LoaderCircle className="mt-0.5 h-4 w-4 shrink-0 animate-spin" />
          <div className="min-w-0">
            <p className="font-bold">
              {hasTargetedRegeneration
                ? `${regeneratingQuestionIds.length}개 질문을 재생성 중입니다.`
                : "질문 전체를 재생성 중입니다."}
            </p>
            <p className="mt-1 break-words text-xs leading-5 text-sky-700 [overflow-wrap:anywhere]">
              완료 전까지 현재 질문은 참고용으로 유지되고, 새 결과가 도착하면 자동으로 갱신됩니다.
            </p>
          </div>
        </div>
      ) : null}

      {errorMessage ? (
        <div className="mt-5 flex items-start gap-2 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span className="break-words [overflow-wrap:anywhere]">{errorMessage}</span>
        </div>
      ) : null}

      {data ? (
        <div className="mt-5 grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-600 md:grid-cols-4">
          {generationOverview.map((item) => (
            <div key={item.label}>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
                {item.label}
              </p>
              <p className={`mt-1 text-base font-semibold ${item.tone}`}>
                {item.value}
              </p>
            </div>
          ))}
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

      <div className="mt-5 grid gap-3 md:grid-cols-5">
        <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] p-4">
          <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
            질문 수
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
            <InterviewSessionQuestionCard
              key={question.id}
              question={question}
              index={index}
              selectable={selectable}
              isSelected={selectedQuestionIds.includes(question.id)}
              selectionDisabled={areQuestionActionsDisabled}
              isRegenerating={isQuestionRegenerating(question.id)}
              interactionDisabled={areQuestionActionsDisabled}
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
