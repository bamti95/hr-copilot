import { formatDashboardNumber, type DashboardSummary } from "../types";
import { DashboardPanel } from "./dashboardShared";

export function HiringPipelinePanel({ data }: { data: DashboardSummary }) {
  const maxPipelineCount = Math.max(...data.pipeline.map((item) => item.count), 1);

  return (
    <DashboardPanel
      title="전체 면접 준비 진행률"
      description="지원자 등록부터 질문 검토까지의 준비 상태입니다."
    >
      <div className="space-y-3">
        {data.pipeline.map((item) => (
          <div key={item.key} className="space-y-1.5">
            <div className="flex items-center justify-between gap-3 text-sm">
              <span className="font-semibold text-slate-700">{item.label}</span>
              <span className="font-bold text-slate-950">
                {formatDashboardNumber(item.count)}
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full bg-[#315fbc]"
                style={{
                  width: `${Math.max((item.count / maxPipelineCount) * 100, 3)}%`,
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </DashboardPanel>
  );
}
