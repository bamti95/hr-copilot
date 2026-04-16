import { SummaryCard } from "../../../../common/components/SummaryCard";
import { StatusPill } from "../../../../common/components/StatusPill";
import { formatNumber } from "../../../../common/utils/format";
import type { DashboardActivity, DashboardMetric } from "../types";

interface DashboardOverviewProps {
  metrics: DashboardMetric[];
  activities: DashboardActivity[];
}

export function DashboardOverview({
  metrics,
  activities,
}: DashboardOverviewProps) {
  return (
    <div className="grid gap-[22px] xl:grid-cols-[1.35fr_0.95fr]">
      <section className="rounded-[32px] border border-white/70 bg-[linear-gradient(135deg,rgba(89,155,255,0.08),rgba(43,211,143,0.08)),var(--panel)] p-7 shadow-[var(--shadow)] backdrop-blur-[14px]">
        <div className="grid gap-[22px] md:grid-cols-2">
          {metrics.map((metric) => (
            <SummaryCard
              key={metric.id}
              icon={metric.icon}
              label={metric.label}
              value={formatNumber(metric.value)}
              hint={metric.hint}
            />
          ))}
        </div>
      </section>

      <section className="rounded-[32px] border border-white/70 bg-[var(--panel)] p-7 shadow-[var(--shadow)] backdrop-blur-[14px]">
        <div className="mb-[18px] flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="m-0 text-2xl font-bold text-[var(--text)]">Operational Snapshot</h2>
            <p className="mt-2 text-sm text-[var(--muted)]">
              오늘 처리해야 할 주요 운영 흐름입니다.
            </p>
          </div>
        </div>
        <div className="flex flex-col gap-3.5">
          {activities.map((activity) => (
            <article
              key={activity.id}
              className="flex items-center justify-between gap-4 rounded-[22px] border border-white/70 bg-white/70 px-5 py-[18px]"
            >
              <div>
                <strong>{activity.title}</strong>
                <p className="m-0 mt-1 text-sm text-[var(--muted)]">
                  {activity.owner} · Due {activity.dueDate}
                </p>
              </div>
              <StatusPill status={activity.status} />
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
