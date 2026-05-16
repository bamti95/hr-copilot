import { Link } from "react-router-dom";
import { CheckCircle2 } from "lucide-react";
import {
  formatDashboardDateTime,
  type DashboardSummary,
} from "../types";
import {
  DashboardPanel,
  getActivityLinkState,
  getActivityTargetPath,
} from "./dashboardShared";

export function RecentActivitiesPanel({ data }: { data: DashboardSummary }) {
  return (
    <DashboardPanel
      title="최근 활동 로그"
      description="생성, 요청, 완료 시각을 합성한 업무 이벤트입니다."
    >
      <div className="space-y-2">
        {data.recentActivities.map((activity) => (
          <Link
            key={activity.id}
            to={getActivityTargetPath(activity.targetPath)}
            state={getActivityLinkState(activity.targetPath)}
            className="flex items-start gap-3 rounded-lg border border-slate-200 bg-white px-3 py-3 text-sm no-underline transition hover:border-[#315fbc] hover:bg-[#f5f8ff]"
          >
            <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-50">
              <CheckCircle2 className="h-4 w-4 text-[#315fbc]" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="font-semibold text-slate-950">{activity.title}</div>
              <div className="mt-1 truncate text-xs text-slate-500">
                {activity.description}
              </div>
            </div>
            <span className="shrink-0 text-xs font-semibold text-slate-400">
              {formatDashboardDateTime(activity.occurredAt)}
            </span>
          </Link>
        ))}
      </div>
    </DashboardPanel>
  );
}
