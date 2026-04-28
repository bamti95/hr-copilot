import {
  Activity,
  AlertTriangle,
  BarChart3,
  Clock3,
  Cpu,
  DollarSign,
  RefreshCw,
  Sigma,
} from "lucide-react";
import type { ReactNode } from "react";
import type {
  LlmUsageCallLog,
  LlmUsageMetric,
  LlmUsageNodeSummary,
  LlmUsageSessionSummary,
} from "../types";

interface LlmUsageOverviewProps {
  metrics: LlmUsageMetric;
  byNode: LlmUsageNodeSummary[];
  bySession: LlmUsageSessionSummary[];
  recentCalls: LlmUsageCallLog[];
  isLoading: boolean;
  error: string | null;
  onRefresh: () => void;
}

const statusClassMap: Record<string, string> = {
  success: "border-emerald-200 bg-emerald-50 text-emerald-700",
  failed: "border-rose-200 bg-rose-50 text-rose-700",
};

function formatNumber(value: number): string {
  return new Intl.NumberFormat("ko-KR").format(value);
}

function formatCost(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 4,
    maximumFractionDigits: 6,
  }).format(value);
}

function formatMs(value: number | null): string {
  if (value === null) {
    return "-";
  }
  if (value >= 1000) {
    return `${(value / 1000).toFixed(2)}초`;
  }
  return `${Math.round(value)}ms`;
}

function formatDateTime(value: string | null): string {
  if (!value) {
    return "-";
  }
  return new Intl.DateTimeFormat("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function MetricCard({
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
    <article className="min-w-0 rounded-[24px] border border-white/70 bg-white/80 p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-3">
        <span className="text-sm font-semibold text-[var(--muted)]">{label}</span>
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-[#eef5ff] text-[#315fbc]">
          {icon}
        </span>
      </div>
      <strong className="block break-words text-[1.55rem] leading-none text-[var(--text)] sm:text-[1.7rem]">
        {value}
      </strong>
      <p className="m-0 mt-2 break-words text-sm text-[var(--muted)]">{hint}</p>
    </article>
  );
}

export function LlmUsageOverview({
  metrics,
  byNode,
  bySession,
  recentCalls,
  isLoading,
  error,
  onRefresh,
}: LlmUsageOverviewProps) {
  const maxNodeCost = Math.max(...byNode.map((node) => node.estimatedCost), 0);

  return (
    <div className="flex min-w-0 flex-col gap-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="전체 토큰"
          value={formatNumber(metrics.totalTokens)}
          hint={`입력 ${formatNumber(metrics.totalInputTokens)} / 출력 ${formatNumber(
            metrics.totalOutputTokens,
          )}`}
          icon={<Sigma className="h-5 w-5" />}
        />
        <MetricCard
          label="예상 비용"
          value={formatCost(metrics.estimatedCost)}
          hint={`${formatNumber(metrics.totalCalls)}회 LLM 호출 기준`}
          icon={<DollarSign className="h-5 w-5" />}
        />
        <MetricCard
          label="평균 호출 시간"
          value={formatMs(metrics.avgElapsedMs)}
          hint="노드별 LLM 호출 평균"
          icon={<Clock3 className="h-5 w-5" />}
        />
        <MetricCard
          label="실패 호출"
          value={formatNumber(metrics.failedCalls)}
          hint="오류 메시지가 함께 저장됩니다"
          icon={<AlertTriangle className="h-5 w-5" />}
        />
      </section>

      <section className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)] sm:p-6">
        <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-[#315fbc]" />
              <h2 className="m-0 text-xl font-bold text-[var(--text)]">
                LangGraph 노드별 사용량
              </h2>
            </div>
            <p className="m-0 mt-1 text-sm text-[var(--muted)]">
              질문 생성 파이프라인의 각 노드가 사용한 토큰, 비용, 평균 시간을 비교합니다.
            </p>
          </div>
          <button
            type="button"
            onClick={onRefresh}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-xl border border-[#315fbc]/20 bg-[#315fbc]/8 px-4 text-sm font-semibold text-[#315fbc] transition hover:bg-[#315fbc]/12"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            새로고침
          </button>
        </div>

        {error ? (
          <div className="mb-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        <div className="grid gap-3">
          {byNode.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-200 bg-white/60 p-8 text-center text-sm text-[var(--muted)]">
              아직 저장된 LLM 호출 로그가 없습니다.
            </div>
          ) : (
            byNode.map((node) => {
              const width =
                maxNodeCost > 0
                  ? Math.max((node.estimatedCost / maxNodeCost) * 100, 4)
                  : 0;
              return (
                <article
                  key={node.nodeName}
                  className="min-w-0 rounded-2xl border border-white/70 bg-white/75 p-4"
                >
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <Cpu className="h-4 w-4 shrink-0 text-[#315fbc]" />
                        <strong className="break-words text-[var(--text)]">
                          {node.nodeName}
                        </strong>
                      </div>
                      <p className="m-0 mt-1 text-sm text-[var(--muted)]">
                        입력 {formatNumber(node.inputTokens)} / 출력{" "}
                        {formatNumber(node.outputTokens)} / 호출{" "}
                        {formatNumber(node.callCount)}회
                      </p>
                    </div>
                    <div className="grid grid-cols-3 gap-3 text-right text-sm">
                      <span>{formatNumber(node.totalTokens)} tok</span>
                      <span>{formatCost(node.estimatedCost)}</span>
                      <span>{formatMs(node.avgElapsedMs)}</span>
                    </div>
                  </div>
                  <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-[#315fbc]"
                      style={{ width: `${width}%` }}
                    />
                  </div>
                </article>
              );
            })
          )}
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="min-w-0 rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)] sm:p-6">
          <h2 className="m-0 text-xl font-bold text-[var(--text)]">세션별 비용 요약</h2>
          <div className="mt-5 overflow-x-auto">
            <table className="w-full min-w-[620px] border-separate border-spacing-y-2 text-left text-sm">
              <thead className="text-xs uppercase text-[var(--muted)]">
                <tr>
                  <th className="px-3 py-2">세션</th>
                  <th className="px-3 py-2">지원자</th>
                  <th className="px-3 py-2 text-right">토큰</th>
                  <th className="px-3 py-2 text-right">비용</th>
                  <th className="px-3 py-2 text-right">평균 시간</th>
                </tr>
              </thead>
              <tbody>
                {bySession.map((session) => (
                  <tr key={session.sessionId} className="bg-white/72">
                    <td className="rounded-l-2xl px-3 py-3 font-semibold">
                      #{session.sessionId}
                    </td>
                    <td className="px-3 py-3">
                      <div className="font-semibold text-[var(--text)]">
                        {session.candidateName}
                      </div>
                      <div className="text-xs text-[var(--muted)]">
                        {session.targetJob} · {formatDateTime(session.lastCalledAt)}
                      </div>
                    </td>
                    <td className="px-3 py-3 text-right">
                      {formatNumber(session.totalTokens)}
                    </td>
                    <td className="px-3 py-3 text-right">
                      {formatCost(session.estimatedCost)}
                    </td>
                    <td className="rounded-r-2xl px-3 py-3 text-right">
                      {formatMs(session.avgElapsedMs)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="min-w-0 rounded-[28px] border border-white/70 bg-[var(--panel)] p-5 shadow-[var(--shadow)] sm:p-6">
          <h2 className="m-0 text-xl font-bold text-[var(--text)]">최근 호출 로그</h2>
          <div className="mt-5 flex flex-col gap-3">
            {recentCalls.map((call) => {
              const normalizedStatus = call.callStatus.toLowerCase();
              return (
                <article
                  key={call.id}
                  className="min-w-0 rounded-2xl border border-white/70 bg-white/75 p-4"
                >
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <Activity className="h-4 w-4 shrink-0 text-[#315fbc]" />
                        <strong className="break-words">
                          {call.nodeName ?? "unknown"}
                        </strong>
                        <span
                          className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${
                            statusClassMap[normalizedStatus] ??
                            "border-slate-200 bg-slate-50 text-slate-600"
                          }`}
                        >
                          {call.callStatus}
                        </span>
                      </div>
                      <p className="m-0 mt-1 text-sm text-[var(--muted)]">
                        {call.candidateName} · 세션 #{call.sessionId} ·{" "}
                        {formatDateTime(call.createdAt)}
                      </p>
                    </div>
                    <div className="text-left text-sm md:text-right">
                      <div className="font-semibold">{call.modelName}</div>
                      <div className="text-[var(--muted)]">
                        {formatNumber(call.totalTokens)} tok ·{" "}
                        {formatCost(call.estimatedCost)} · {formatMs(call.elapsedMs)}
                      </div>
                    </div>
                  </div>
                  {call.errorMessage ? (
                    <p className="m-0 mt-3 break-words rounded-xl bg-rose-50 px-3 py-2 text-xs text-rose-700 [overflow-wrap:anywhere]">
                      {call.errorMessage}
                    </p>
                  ) : null}
                </article>
              );
            })}
          </div>
        </div>
      </section>
    </div>
  );
}
