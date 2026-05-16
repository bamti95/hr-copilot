import { Link } from "react-router-dom";
import { ArrowRight, Timer } from "lucide-react";
import {
  formatDashboardCurrency,
  formatDashboardNumber,
  formatDashboardSeconds,
  type DashboardSummary,
} from "../types";
import { businessNodeLabel, DashboardPanel, EmptyState } from "./dashboardShared";

export function AiCostPanel({
  data,
  isLoading,
}: {
  data: DashboardSummary;
  isLoading: boolean;
}) {
  const topNode = data.llmCost.topCostNode;
  const estimatedTodayCost =
    data.llmCost.todayCost +
    data.jobPosting.estimatedNextAnalysisCost * data.jobPosting.pendingAnalysisCount;

  return (
    <DashboardPanel
      title="AI 운영 비용"
      description="오늘 사용액과 오늘 남은 작업을 반영한 예상 비용입니다."
    >
      <div className="grid gap-3 sm:grid-cols-2">
        <CostStat
          label="오늘 사용"
          value={formatDashboardCurrency(data.llmCost.todayCost)}
          isLoading={isLoading}
        />
        <CostStat
          label="오늘 예상"
          value={formatDashboardCurrency(estimatedTodayCost)}
          isLoading={isLoading}
        />
        <CostStat
          label="이번 달 누적"
          value={formatDashboardCurrency(data.llmCost.monthCost)}
          isLoading={isLoading}
        />
        <CostStat
          label="오늘 호출"
          value={`${formatDashboardNumber(data.llmCost.todayCalls)}회`}
          isLoading={isLoading}
        />
      </div>

      <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="m-0 text-xs font-bold uppercase text-slate-500">
              비용이 가장 큰 업무
            </p>
            <p className="m-0 mt-1 truncate text-sm font-bold text-slate-950">
              {topNode ? businessNodeLabel(topNode.nodeName) : "-"}
            </p>
          </div>
          <div className="shrink-0 text-right">
            <p className="m-0 text-sm font-bold text-slate-950">
              {topNode ? formatDashboardCurrency(topNode.estimatedCost) : "-"}
            </p>
            <p className="m-0 mt-1 text-xs font-semibold text-slate-500">
              {topNode ? formatDashboardSeconds(topNode.avgElapsedMs) : "-"}
            </p>
          </div>
        </div>
      </div>

      <Link
        to="/manager/llm-usage"
        className="mt-4 inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-[#315fbc] px-3 text-sm font-bold text-[#315fbc] no-underline transition hover:bg-[#f5f8ff]"
      >
        AI 비용 상세 보기
        <ArrowRight className="h-4 w-4" />
      </Link>
    </DashboardPanel>
  );
}

export function CostByWorkPanel({
  data,
  isLoading,
}: {
  data: DashboardSummary;
  isLoading: boolean;
}) {
  const maxCost = Math.max(
    ...data.llmCost.topNodes.map((node) => node.estimatedCost),
    0.000001,
  );

  return (
    <DashboardPanel
      title="업무별 AI 비용 Top 5"
      description="기술 노드명이 아니라 채용 업무 기준으로 표시합니다."
    >
      <div className="space-y-3">
        {data.llmCost.topNodes.length === 0 ? (
          <EmptyState text="집계된 AI 비용이 없습니다." />
        ) : (
          data.llmCost.topNodes.map((node) => (
            <div key={node.nodeName} className="space-y-1.5">
              <div className="flex items-center justify-between gap-3 text-sm">
                <span className="min-w-0 truncate font-semibold text-slate-700">
                  {businessNodeLabel(node.nodeName)}
                </span>
                <span className="shrink-0 font-bold text-slate-950">
                  {isLoading
                    ? "-"
                    : `${formatDashboardCurrency(node.estimatedCost)} · ${formatDashboardNumber(
                        node.callCount,
                      )}회`}
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-emerald-500"
                  style={{
                    width: `${Math.max((node.estimatedCost / maxCost) * 100, 3)}%`,
                  }}
                />
              </div>
              <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
                <span>{formatDashboardNumber(node.totalTokens)} tokens</span>
                <span className="inline-flex items-center gap-1">
                  <Timer className="h-3.5 w-3.5" />
                  {formatDashboardSeconds(node.avgElapsedMs)}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </DashboardPanel>
  );
}

function CostStat({
  label,
  value,
  isLoading,
}: {
  label: string;
  value: string;
  isLoading: boolean;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-4 py-3">
      <p className="m-0 text-xs font-semibold text-slate-500">{label}</p>
      <p className="m-0 mt-1 text-lg font-bold text-slate-950">
        {isLoading ? "-" : value}
      </p>
    </div>
  );
}
