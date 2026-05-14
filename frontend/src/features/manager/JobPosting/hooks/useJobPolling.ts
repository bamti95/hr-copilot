import { useCallback, useEffect, useRef, useState } from "react";
import type { JobPostingAiJob } from "../types";
import { isTerminalJob } from "../utils/jobStatus";

interface UseJobPollingOptions {
  fetcher: (jobId: number) => Promise<JobPostingAiJob>;
  intervalMs?: number;
  maxPollingMs?: number;
  onCompleted?: (job: JobPostingAiJob) => void | Promise<void>;
  onFailed?: (job: JobPostingAiJob) => void;
  onError?: (error: unknown) => void;
  onTimeout?: (job: JobPostingAiJob) => void;
}

export function useJobPolling({
  fetcher,
  intervalMs = 1500,
  maxPollingMs,
  onCompleted,
  onFailed,
  onError,
  onTimeout,
}: UseJobPollingOptions) {
  const [job, setJob] = useState<JobPostingAiJob | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const isHandlingTerminalRef = useRef(false);
  const pollingStartedAtRef = useRef<number | null>(null);
  const fetcherRef = useRef(fetcher);
  const onCompletedRef = useRef(onCompleted);
  const onFailedRef = useRef(onFailed);
  const onErrorRef = useRef(onError);
  const onTimeoutRef = useRef(onTimeout);

  useEffect(() => {
    fetcherRef.current = fetcher;
    onCompletedRef.current = onCompleted;
    onFailedRef.current = onFailed;
    onErrorRef.current = onError;
    onTimeoutRef.current = onTimeout;
  }, [fetcher, onCompleted, onError, onFailed, onTimeout]);

  const startPolling = useCallback((nextJob: JobPostingAiJob) => {
    isHandlingTerminalRef.current = false;
    pollingStartedAtRef.current = Date.now();
    setJob(nextJob);
    setIsPolling(!isTerminalJob(nextJob));
  }, []);

  const stopPolling = useCallback(() => {
    pollingStartedAtRef.current = null;
    setIsPolling(false);
  }, []);

  const clearJob = useCallback(() => {
    isHandlingTerminalRef.current = false;
    pollingStartedAtRef.current = null;
    setJob(null);
    setIsPolling(false);
  }, []);

  useEffect(() => {
    if (!job || !isPolling) {
      return;
    }

    let cancelled = false;
    let timer: number | undefined;

    const tick = async () => {
      if (
        maxPollingMs &&
        pollingStartedAtRef.current &&
        Date.now() - pollingStartedAtRef.current >= maxPollingMs
      ) {
        setIsPolling(false);
        pollingStartedAtRef.current = null;
        onTimeoutRef.current?.(job);
        return;
      }

      try {
        const nextJob = await fetcherRef.current(job.jobId);
        if (cancelled) {
          return;
        }

        setJob(nextJob);
        if (isTerminalJob(nextJob)) {
          if (isHandlingTerminalRef.current) {
            return;
          }
          isHandlingTerminalRef.current = true;
          setIsPolling(false);
          pollingStartedAtRef.current = null;
          if (nextJob.status === "SUCCESS") {
            await onCompletedRef.current?.(nextJob);
          } else {
            onFailedRef.current?.(nextJob);
          }
          return;
        }

        timer = window.setTimeout(() => {
          void tick();
        }, intervalMs);
      } catch (error) {
        if (!cancelled) {
          setIsPolling(false);
          pollingStartedAtRef.current = null;
          onErrorRef.current?.(error);
        }
      }
    };

    timer = window.setTimeout(() => {
      void tick();
    }, 0);

    return () => {
      cancelled = true;
      if (timer !== undefined) {
        window.clearTimeout(timer);
      }
    };
  }, [intervalMs, isPolling, job?.jobId, maxPollingMs]);

  return {
    job,
    isPolling,
    setJob,
    startPolling,
    stopPolling,
    clearJob,
  };
}
