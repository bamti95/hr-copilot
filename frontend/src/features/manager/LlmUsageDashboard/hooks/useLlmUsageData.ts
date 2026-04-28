import { useCallback, useEffect, useState } from "react";
import { fetchLlmUsageSummary } from "../services/llmUsageService";
import type { LlmUsageSummaryResponse } from "../types";

export function useLlmUsageData() {
  const [data, setData] = useState<LlmUsageSummaryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetchLlmUsageSummary();
      setData(response);
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

  return {
    data,
    isLoading,
    error,
    reload: load,
  };
}
