import {
  dashboardActivities,
  dashboardMetrics,
} from "../../../../common/data/managerConsoleData";

export function fetchDashboardMetrics() {
  return dashboardMetrics;
}

export function fetchDashboardActivities() {
  return dashboardActivities;
}
