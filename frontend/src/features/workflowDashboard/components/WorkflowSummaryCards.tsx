import { CheckCircle2, Clock3, DollarSign, GitBranch, Sigma, Split } from "lucide-react";
import type { ReactNode } from "react";
import {
  formatCost,
  formatMs,
  formatNumber,
  type LlmUsageMetric,
} from "../types/workflowDashboard.types";

interface WorkflowSummaryCardsProps {
  metrics: LlmUsageMetric;
  totalSessions: number;
  totalSessionCost: number;
}

function SummaryCard({
  label,
  value,
  hint,
  icon,
}: {
  label: string;
  value: string;
  hint: string;
  icon: ReactNode;
}) {
  return (
    <article className="min-w-0 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between gap-3">
        <span className="text-sm font-semibold text-slate-500">{label}</span>
        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-[#eef5ff] text-[#315fbc]">
          {icon}
        </span>
      </div>
      <strong className="block truncate text-2xl leading-none text-slate-950">
        {value}
      </strong>
      <p className="m-0 mt-2 text-xs text-slate-500">{hint}</p>
    </article>
  );
}

export function WorkflowSummaryCards({
  metrics,
  totalSessions,
  totalSessionCost,
}: WorkflowSummaryCardsProps) {
  const failedCalls = metrics.failedCalls;
  const successRate =
    metrics.totalCalls > 0
      ? ((metrics.totalCalls - failedCalls) / metrics.totalCalls) * 100
      : 0;

  return (
    <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
      <SummaryCard
        label="총 세션 수"
        value={formatNumber(totalSessions)}
        hint="질문 생성 실행 단위"
        icon={<GitBranch className="h-4 w-4" />}
      />
      <SummaryCard
        label="성공률"
        value={`${successRate.toFixed(1)}%`}
        hint={`실패 호출 ${formatNumber(failedCalls)}건`}
        icon={<CheckCircle2 className="h-4 w-4" />}
      />
      <SummaryCard
        label="평균 실행시간"
        value={formatMs(metrics.avgElapsedMs)}
        hint="LLM/노드 호출 평균"
        icon={<Clock3 className="h-4 w-4" />}
      />
      <SummaryCard
        label="총 토큰"
        value={formatNumber(metrics.totalTokens)}
        hint={`입력 ${formatNumber(metrics.totalInputTokens)} 토큰`}
        icon={<Sigma className="h-4 w-4" />}
      />
      <SummaryCard
        label="총 비용"
        value={formatCost(metrics.estimatedCost || totalSessionCost)}
        hint="예상 USD 비용"
        icon={<DollarSign className="h-4 w-4" />}
      />
      <SummaryCard
        label="평균 질문 수"
        value="미제공"
        hint="세션별 최종 질문 집계 API 필요"
        icon={<Split className="h-4 w-4" />}
      />
    </section>
  );
}

