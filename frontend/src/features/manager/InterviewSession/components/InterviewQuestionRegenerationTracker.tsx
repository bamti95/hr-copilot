import { useEffect, useMemo } from "react";
import { LoaderCircle } from "lucide-react";
import { fetchInterviewQuestionGenerationStatus } from "../services/interviewSessionService";
import type { InterviewQuestionGenerationStatus } from "../types";
import { useInterviewQuestionRegenerationStore } from "../store/interviewQuestionRegenerationStore";

const RUNNING_STATUSES = new Set<InterviewQuestionGenerationStatus>([
  "QUEUED",
  "PROCESSING",
]);

const POLL_INTERVAL_MS = 3000;

function isRunningStatus(status: InterviewQuestionGenerationStatus) {
  return RUNNING_STATUSES.has(status);
}

/**
 * 면접 세션 질문 재생성 작업을 화면과 무관하게 폴링한다.
 * ManagerLayout에 마운트해 다른 페이지로 이동해도 완료까지 추적한다.
 */
export function InterviewQuestionRegenerationTracker() {
  const jobs = useInterviewQuestionRegenerationStore((state) => state.jobs);
  const updateJob = useInterviewQuestionRegenerationStore((state) => state.updateJob);
  const completeJob = useInterviewQuestionRegenerationStore((state) => state.completeJob);

  const sessionIdsKey = useMemo(
    () =>
      Object.keys(jobs)
        .map(Number)
        .sort((a, b) => a - b)
        .join(","),
    [jobs],
  );

  useEffect(() => {
    if (!sessionIdsKey) {
      return;
    }

    const activeSessionIds = sessionIdsKey.split(",").map(Number);
    let cancelled = false;

    const pollAll = async () => {
      for (const sessionId of activeSessionIds) {
        if (cancelled) {
          return;
        }

        const job = useInterviewQuestionRegenerationStore.getState().jobs[sessionId];
        if (!job) {
          continue;
        }

        try {
          const status = await fetchInterviewQuestionGenerationStatus(sessionId);
          if (cancelled) {
            return;
          }

          const currentJob =
            useInterviewQuestionRegenerationStore.getState().jobs[sessionId];
          if (!currentJob) {
            continue;
          }

          const running = isRunningStatus(status.status);
          let hasObservedRunning = currentJob.hasObservedRunning;

          if (running) {
            hasObservedRunning = true;
          }

          const baselineCompletedAt =
            currentJob.completedAtBaseline ?? status.completedAt;
          const baselineRequestedAt =
            currentJob.requestedAtBaseline ?? status.requestedAt;

          if (!currentJob.baselineCaptured) {
            updateJob(sessionId, {
              completedAtBaseline: status.completedAt,
              requestedAtBaseline: status.requestedAt,
              hasObservedRunning,
              baselineCaptured: true,
            });
          } else if (hasObservedRunning !== currentJob.hasObservedRunning) {
            updateJob(sessionId, { hasObservedRunning });
          }

          if (running) {
            continue;
          }

          const hasNewCompletedResult =
            baselineCompletedAt !== null &&
            status.completedAt !== baselineCompletedAt;

          if (hasObservedRunning || hasNewCompletedResult) {
            completeJob(sessionId);
          }
        } catch {
          // 네트워크 오류 시 다음 폴링에서 재시도한다.
        }
      }
    };

    void pollAll();
    const timer = window.setInterval(() => {
      void pollAll();
    }, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [sessionIdsKey, completeJob, updateJob]);

  return null;
}

export function InterviewQuestionRegenerationBanner() {
  const jobsRecord = useInterviewQuestionRegenerationStore((state) => state.jobs);
  const jobs = useMemo(() => Object.values(jobsRecord), [jobsRecord]);

  if (jobs.length === 0) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-900">
      <div className="flex items-start gap-3">
        <LoaderCircle className="mt-0.5 h-4 w-4 shrink-0 animate-spin text-sky-700" />
        <div className="min-w-0 space-y-1">
          <p className="font-semibold">면접 질문 재생성이 백그라운드에서 진행 중입니다</p>
          <ul className="space-y-0.5 text-xs leading-5 text-sky-800">
            {jobs.map((job) => (
              <li key={job.sessionId}>
                세션 #{job.sessionId}
                {job.candidateName ? ` · ${job.candidateName}` : ""}
                {job.targetQuestionIds.length > 0
                  ? ` · ${job.targetQuestionIds.length}개 질문`
                  : " · 전체 질문"}
              </li>
            ))}
          </ul>
          <p className="text-xs text-sky-700">
            다른 화면으로 이동해도 작업은 계속됩니다. 완료 후 세션 상세에서 결과를 확인할 수
            있습니다.
          </p>
        </div>
      </div>
    </div>
  );
}