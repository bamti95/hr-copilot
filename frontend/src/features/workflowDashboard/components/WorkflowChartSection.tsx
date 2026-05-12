import { BarChart3, RefreshCw } from "lucide-react";
import type { ReactNode } from "react";
import {
  formatCost,
  getWorkflowExecutionId,
  formatMs,
  formatNumber,
  type LlmUsageMetric,
  type LlmUsageNodeSummary,
  type LlmUsageSessionSummary,
} from "../types/workflowDashboard.types";

interface WorkflowChartSectionProps {
  metrics: LlmUsageMetric;
  byNode: LlmUsageNodeSummary[];
  bySession: LlmUsageSessionSummary[];
  isLoading: boolean;
  error: string | null;
  onRefresh: () => void;
}

export function WorkflowChartSection({
  metrics,
  byNode,
  bySession,
  isLoading,
  error,
  onRefresh,
}: WorkflowChartSectionProps) {
  const failedCalls = metrics.failedCalls;
  const maxLatency = Math.max(...byNode.map((node) => node.avgElapsedMs), 1);
  const maxTokens = Math.max(...byNode.map((node) => node.totalTokens), 1);
  const costTrendMax = Math.max(
    ...bySession.slice(0, 8).map((session) => session.estimatedCost),
    1,
  );

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-[#315fbc]" />
          <h2 className="m-0 text-lg font-bold text-slate-950">워크플로우 운영 현황</h2>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-[#315fbc]/20 bg-[#315fbc]/8 px-4 text-sm font-semibold text-[#315fbc] transition hover:bg-[#315fbc]/12"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          새로고침
        </button>
      </div>

      {error ? (
        <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {error}
        </div>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-4">
        <ChartCard title="노드별 평균 실행시간">
          {byNode.slice(0, 8).map((node) => (
            <BarRow
              key={node.nodeName}
              label={node.nodeName}
              value={formatMs(node.avgElapsedMs)}
              width={(node.avgElapsedMs / maxLatency) * 100}
              color="bg-[#315fbc]"
            />
          ))}
        </ChartCard>

        <ChartCard title="토큰 사용량">
          {byNode.slice(0, 8).map((node) => (
            <div key={node.nodeName} className="space-y-1">
              <div className="flex justify-between gap-2 text-xs">
                <span className="truncate text-slate-600">{node.nodeName}</span>
                <span className="text-slate-500">{formatNumber(node.totalTokens)}</span>
              </div>
              <div className="flex h-2 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="bg-[#315fbc]"
                  style={{ width: `${Math.max((node.inputTokens / maxTokens) * 100, 2)}%` }}
                />
                <div
                  className="bg-[#23a094]"
                  style={{ width: `${Math.max((node.outputTokens / maxTokens) * 100, 2)}%` }}
                />
              </div>
            </div>
          ))}
        </ChartCard>

        <ChartCard title="비용 추이">
          <div className="flex h-[132px] items-end gap-2">
            {bySession
              .slice(0, 8)
              .reverse()
              .map((session) => {
                const executionId = getWorkflowExecutionId(session);
                return (
                <div key={executionId ?? session.lastCalledAt} className="flex min-w-0 flex-1 flex-col items-center gap-2">
                  <div
                    className="w-full rounded-t bg-[#315fbc]"
                    style={{
                      height: `${Math.max((session.estimatedCost / costTrendMax) * 104, 4)}px`,
                    }}
                    title={formatCost(session.estimatedCost)}
                  />
                  <span className="max-w-full truncate text-[10px] text-slate-500">
                    #{executionId ?? "-"}
                  </span>
                </div>
              );
              })}
          </div>
        </ChartCard>

        <ChartCard title="성공/실패 비율">
          <div className="grid h-full content-center gap-3">
            <StatusBar label="성공" count={metrics.totalCalls - failedCalls} color="bg-emerald-500" />
            <StatusBar label="실패" count={failedCalls} color="bg-rose-500" />
            <StatusBar label="재시도" count={0} color="bg-amber-500" />
            <StatusBar label="건너뜀" count={0} color="bg-slate-400" />
          </div>
        </ChartCard>
      </div>
    </section>
  );
}

function ChartCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <article className="min-h-[190px] rounded-lg border border-slate-200 bg-slate-50 p-4">
      <h3 className="m-0 mb-3 text-sm font-bold text-slate-900">{title}</h3>
      <div className="space-y-3">{children}</div>
    </article>
  );
}

function BarRow({
  label,
  value,
  width,
  color,
}: {
  label: string;
  value: string;
  width: number;
  color: string;
}) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between gap-2 text-xs">
        <span className="truncate text-slate-600">{label}</span>
        <span className="text-slate-500">{value}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-white">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.max(width, 2)}%` }} />
      </div>
    </div>
  );
}

function StatusBar({ label, count, color }: { label: string; count: number; color: string }) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs">
        <span className="text-slate-600">{label}</span>
        <span className="font-semibold text-slate-900">{formatNumber(count)}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-white">
        <div className={`h-full w-2/3 rounded-full ${color}`} />
      </div>
    </div>
  );
}
