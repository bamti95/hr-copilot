import { useCallback, useEffect, useRef, useState } from "react";
import type { JobPostingAiJob } from "../types";
import { isTerminalJob } from "../utils/jobStatus";

interface UseJobPollingOptions {
  fetcher: (jobId: number) => Promise<JobPostingAiJob>;
  intervalMs?: number;
  onCompleted?: (job: JobPostingAiJob) => void | Promise<void>;
  onFailed?: (job: JobPostingAiJob) => void;
  onError?: (error: unknown) => void;
}

export function useJobPolling({
  fetcher,
  intervalMs = 1500,
  onCompleted,
  onFailed,
  onError,
}: UseJobPollingOptions) {
  const [job, setJob] = useState<JobPostingAiJob | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const isHandlingTerminalRef = useRef(false);
  const fetcherRef = useRef(fetcher);
  const onCompletedRef = useRef(onCompleted);
  const onFailedRef = useRef(onFailed);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    fetcherRef.current = fetcher;
    onCompletedRef.current = onCompleted;
    onFailedRef.current = onFailed;
    onErrorRef.current = onError;
  }, [fetcher, onCompleted, onError, onFailed]);

  const startPolling = useCallback((nextJob: JobPostingAiJob) => {
    isHandlingTerminalRef.current = false;
    setJob(nextJob);
    setIsPolling(!isTerminalJob(nextJob));
  }, []);

  const stopPolling = useCallback(() => {
    setIsPolling(false);
  }, []);

  const clearJob = useCallback(() => {
    isHandlingTerminalRef.current = false;
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
  }, [intervalMs, isPolling, job?.jobId]);

  return {
    job,
    isPolling,
    setJob,
    startPolling,
    stopPolling,
    clearJob,
  };
}
