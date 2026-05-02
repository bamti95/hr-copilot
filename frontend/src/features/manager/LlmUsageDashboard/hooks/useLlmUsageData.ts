import { useCallback, useEffect, useState } from "react";
import {
  fetchLlmUsageSummary,
  fetchSessionLlmLogs,
} from "../services/llmUsageService";
import type { LlmCallLogListResponse, LlmUsageSummaryResponse } from "../types";

export function useLlmUsageData() {
  const [data, setData] = useState<LlmUsageSummaryResponse | null>(null);
  const [workflowLogs, setWorkflowLogs] = useState<LlmCallLogListResponse | null>(
    null,
  );
  const [isLoading, setIsLoading] = useState(true);
  const [isTraceLoading, setIsTraceLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [traceError, setTraceError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setTraceError(null);
    try {
      const response = await fetchLlmUsageSummary();
      setData(response);
      const firstSessionId = response.bySession[0]?.sessionId;
      if (firstSessionId) {
        setIsTraceLoading(true);
        try {
          setWorkflowLogs(await fetchSessionLlmLogs(firstSessionId));
        } catch (err) {
          setTraceError(
            err instanceof Error
              ? err.message
              : "Workflow trace logs could not be loaded.",
          );
        } finally {
          setIsTraceLoading(false);
        }
      } else {
        setWorkflowLogs(null);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "LLM 사용량 데이터를 불러오지 못했습니다.",
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const loadWorkflowLogs = useCallback(async (sessionId: number) => {
    setIsTraceLoading(true);
    setTraceError(null);
    try {
      setWorkflowLogs(await fetchSessionLlmLogs(sessionId));
    } catch (err) {
      setTraceError(
        err instanceof Error
          ? err.message
          : "Workflow trace logs could not be loaded.",
      );
    } finally {
      setIsTraceLoading(false);
    }
  }, []);

  return {
    data,
    workflowLogs,
    isLoading,
    isTraceLoading,
    error,
    traceError,
    reload: load,
    loadWorkflowLogs,
  };
}
