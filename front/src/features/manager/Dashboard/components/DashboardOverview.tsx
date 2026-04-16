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
    <div className="manager-grid">
      <section className="panel panel--metrics">
        <div className="summary-grid">
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

      <section className="panel">
        <div className="panel__header">
          <div>
            <h2>Operational Snapshot</h2>
            <p>오늘 처리해야 할 주요 운영 흐름입니다.</p>
          </div>
        </div>
        <div className="activity-list">
          {activities.map((activity) => (
            <article key={activity.id} className="activity-card">
              <div>
                <strong>{activity.title}</strong>
                <p>
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
