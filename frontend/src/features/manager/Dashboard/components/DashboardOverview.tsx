import { AiCostPanel, CostByWorkPanel } from "./AiCostPanel";
import { DashboardHeader } from "./DashboardHeader";
import { HiringPipelinePanel } from "./HiringPipelinePanel";
import { JobPostingRagPanel } from "./JobPostingRagPanel";
import { KpiGrid } from "./KpiGrid";
import { PriorityCandidatesTable } from "./PriorityCandidatesTable";
import { RecentActivitiesPanel } from "./RecentActivitiesPanel";
import { RecentSessionsPanel } from "./RecentSessionsPanel";
import { TodayWorkPanel } from "./TodayWorkPanel";
import type { DashboardSummary } from "../types";

interface DashboardOverviewProps {
  data: DashboardSummary;
  isLoading: boolean;
  error: string | null;
  onRefresh: () => void;
}

export function DashboardOverview({
  data,
  isLoading,
  error,
  onRefresh,
}: DashboardOverviewProps) {
  return (
    <div className="space-y-5">
      <DashboardHeader onRefresh={onRefresh} isLoading={isLoading} />

      {error ? (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm font-semibold text-rose-700">
          {error}
        </div>
      ) : null}

      <KpiGrid data={data} isLoading={isLoading} />

      <section className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
        <TodayWorkPanel data={data} />
        <AiCostPanel data={data} isLoading={isLoading} />
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <JobPostingRagPanel data={data} isLoading={isLoading} />
      </section>

      <section className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
        <HiringPipelinePanel data={data} />
        <CostByWorkPanel data={data} isLoading={isLoading} />
      </section>

      <PriorityCandidatesTable data={data} />

      <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <RecentSessionsPanel data={data} />
        <RecentActivitiesPanel data={data} />
      </section>
    </div>
  );
}
