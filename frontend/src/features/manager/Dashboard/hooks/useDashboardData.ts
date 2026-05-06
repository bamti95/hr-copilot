import { useCallback, useEffect, useState } from "react";
import { fetchDashboardSummary } from "../services/dashboardService";
import {
  emptyDashboardSummary,
  type DashboardSummary,
} from "../types";

export function useDashboardData() {
  const [data, setData] = useState<DashboardSummary>(emptyDashboardSummary);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const summary = await fetchDashboardSummary();
      setData(summary);
    } catch (fetchError) {
      setError(
        fetchError instanceof Error
          ? fetchError.message
          : "대시보드 데이터를 불러오지 못했습니다.",
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return {
    data,
    isLoading,
    error,
    reload,
  };
}
