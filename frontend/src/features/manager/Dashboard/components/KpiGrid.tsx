import type { LucideIcon } from "lucide-react";
import {
  AlertCircle,
  ClipboardList,
  DollarSign,
  FileSearch,
  FileText,
  ListChecks,
} from "lucide-react";
import {
  formatDashboardCurrency,
  formatDashboardNumber,
  type DashboardSummary,
} from "../types";

const kpiItems: Array<{
  key: keyof DashboardSummary["kpis"];
  label: string;
  hint: string;
  icon: LucideIcon;
  tone: string;
}> = [
  {
    key: "todayTodoCount",
    label: "오늘 처리 필요",
    hint: "대기, 실패, 검토 필요 업무",
    icon: AlertCircle,
    tone: "text-rose-600",
  },
  {
    key: "documentAnalyzedCount",
    label: "지원자 문서 준비",
    hint: "분석 완료된 지원자",
    icon: FileText,
    tone: "text-emerald-600",
  },
  {
    key: "questionPendingCount",
    label: "질문 생성 대기",
    hint: "면접 질문 준비 중",
    icon: ClipboardList,
    tone: "text-sky-600",
  },
  {
    key: "reviewRequiredCount",
    label: "질문 검토 필요",
    hint: "실패, 일부 완료, 낮은 점수",
    icon: ListChecks,
    tone: "text-amber-600",
  },
];

export function KpiGrid({
  data,
  isLoading,
}: {
  data: DashboardSummary;
  isLoading: boolean;
}) {
  const estimatedTodayCost =
    data.llmCost.todayCost +
    data.jobPosting.estimatedNextAnalysisCost * data.jobPosting.pendingAnalysisCount;

  return (
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
      {kpiItems.map((item) => (
        <MetricCard
          key={item.key}
          icon={item.icon}
          label={item.label}
          value={formatDashboardNumber(data.kpis[item.key])}
          hint={item.hint}
          tone={item.tone}
          isLoading={isLoading}
        />
      ))}
      <MetricCard
        icon={FileSearch}
        label="공고 분석 필요"
        value={formatDashboardNumber(data.jobPosting.reviewRequiredCount)}
        hint={`진행 중 ${formatDashboardNumber(data.jobPosting.pendingAnalysisCount)}건`}
        tone="text-violet-600"
        isLoading={isLoading}
      />
      <MetricCard
        icon={DollarSign}
        label="오늘 예상 AI 비용"
        value={formatDashboardCurrency(data.llmCost.todayCost)}
        hint={`남은 공고 포함 ${formatDashboardCurrency(estimatedTodayCost)}`}
        tone="text-emerald-600"
        isLoading={isLoading}
      />
    </section>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
  hint,
  tone,
  isLoading,
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  hint: string;
  tone: string;
  isLoading: boolean;
}) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="m-0 text-sm font-semibold text-slate-500">{label}</p>
          <strong className="mt-2 block truncate text-2xl font-bold text-slate-950 sm:text-3xl">
            {isLoading ? "-" : value}
          </strong>
        </div>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-50">
          <Icon className={`h-5 w-5 ${tone}`} />
        </div>
      </div>
      <p className="m-0 text-xs font-medium leading-5 text-slate-500">{hint}</p>
    </article>
  );
}
