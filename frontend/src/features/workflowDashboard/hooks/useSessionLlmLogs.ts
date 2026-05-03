import { useCallback, useState } from "react";
import { fetchSessionLlmLogs } from "../services/workflowDashboardApi";
import type { LlmCallLogListResponse } from "../types/workflowDashboard.types";

export function useSessionLlmLogs() {
  const [workflowLogs, setWorkflowLogs] = useState<LlmCallLogListResponse | null>(
    null,
  );
  const [isTraceLoading, setIsTraceLoading] = useState(false);
  const [traceError, setTraceError] = useState<string | null>(null);

  const loadSessionLogs = useCallback(async (sessionId: number) => {
    setIsTraceLoading(true);
    setTraceError(null);
    try {
      setWorkflowLogs(await fetchSessionLlmLogs(sessionId));
    } catch (err) {
      setTraceError(
        err instanceof Error
          ? err.message
          : "노드 실행 로그를 불러오지 못했습니다.",
      );
    } finally {
      setIsTraceLoading(false);
    }
  }, []);

  return { workflowLogs, isTraceLoading, traceError, loadSessionLogs };
}
