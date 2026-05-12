import { useCallback, useEffect, useState } from "react";
import { fetchWorkflowSessions } from "../services/workflowDashboardApi";
import type {
  LlmUsageSummaryResponse,
  WorkflowPipelineType,
} from "../types/workflowDashboard.types";

export function useWorkflowSessions(
  pipelineType: WorkflowPipelineType = "INTERVIEW_QUESTION",
) {
  const [data, setData] = useState<LlmUsageSummaryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setData(await fetchWorkflowSessions(pipelineType));
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "워크플로우 세션 요약을 불러오지 못했습니다.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [pipelineType]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { data, isLoading, error, reload };
}
