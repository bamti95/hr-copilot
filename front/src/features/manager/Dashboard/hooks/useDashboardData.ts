import { fetchDashboardActivities, fetchDashboardMetrics } from "../services/dashboardService";

export function useDashboardData() {
  return {
    metrics: fetchDashboardMetrics(),
    activities: fetchDashboardActivities(),
  };
}
