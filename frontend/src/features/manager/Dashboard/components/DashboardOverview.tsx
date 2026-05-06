import { Link } from "react-router-dom";
import type { ReactNode } from "react";
import {
  AlertCircle,
  ArrowRight,
  Bot,
  CheckCircle2,
  ClipboardList,
  DollarSign,
  FileText,
  ListChecks,
  RefreshCw,
  Timer,
} from "lucide-react";
import {
  formatDashboardCurrency,
  formatDashboardDateTime,
  formatDashboardNumber,
  formatDashboardSeconds,
  priorityClasses,
  priorityLabel,
  statusClasses,
  statusLabel,
  type DashboardPriority,
  type DashboardSummary,
} from "../types";

interface DashboardOverviewProps {
  data: DashboardSummary;
  isLoading: boolean;
  error: string | null;
  onRefresh: () => void;
}

const kpiItems = [
  {
    key: "todayTodoCount",
    label: "오늘 처리 필요",
    hint: "대기·실패·검토 필요 업무",
    icon: AlertCircle,
    tone: "text-rose-600",
  },
  {
    key: "documentAnalyzedCount",
    label: "문서 분석 완료",
    hint: "분석 가능한 지원자",
    icon: FileText,
    tone: "text-emerald-600",
  },
  {
    key: "questionPendingCount",
    label: "질문 생성 대기",
    hint: "미요청·대기·생성 중 세션",
    icon: ClipboardList,
    tone: "text-sky-600",
  },
  {
    key: "reviewRequiredCount",
    label: "검토 필요",
    hint: "실패·일부 완료·낮은 점수",
    icon: ListChecks,
    tone: "text-amber-600",
  },
] as const;

export function DashboardOverview({
  data,
  isLoading,
  error,
  onRefresh,
}: DashboardOverviewProps) {
  const maxPipelineCount = Math.max(
    ...data.pipeline.map((item) => item.count),
    1,
  );
  const sessionLinkState = (sessionId: number | null | undefined) =>
    sessionId ? { openDetailSessionId: sessionId } : undefined;

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="m-0 text-lg font-bold text-slate-950">
            오늘의 채용 준비 현황
          </h2>
          <p className="m-0 mt-1 text-sm text-slate-500">
            지원자 분석, 질문 생성, 검토 필요 업무를 한 화면에서 확인합니다.
          </p>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 transition hover:border-[#315fbc] hover:text-[#315fbc]"
        >
          <RefreshCw className="h-4 w-4" />
          새로고침
        </button>
      </div>

      {error ? (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm font-semibold text-rose-700">
          {error}
        </div>
      ) : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
        {kpiItems.map((item) => {
          const Icon = item.icon;
          const value = data.kpis[item.key];
          return (
            <article
              key={item.key}
              className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
            >
              <div className="mb-4 flex items-start justify-between gap-3">
                <div>
                  <p className="m-0 text-sm font-semibold text-slate-500">
                    {item.label}
                  </p>
                  <strong className="mt-2 block text-3xl font-bold text-slate-950">
                    {isLoading ? "-" : formatDashboardNumber(value)}
                  </strong>
                </div>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-50">
                  <Icon className={`h-5 w-5 ${item.tone}`} />
                </div>
              </div>
              <p className="m-0 text-xs font-medium text-slate-500">{item.hint}</p>
            </article>
          );
        })}
        <MetricCard
          icon={DollarSign}
          label="오늘 LLM 비용"
          value={formatDashboardCurrency(data.llmCost.todayCost)}
          hint={`이번 달 ${formatDashboardCurrency(data.llmCost.monthCost)}`}
          tone="text-emerald-600"
          isLoading={isLoading}
        />
        <MetricCard
          icon={Bot}
          label="오늘 LLM 호출"
          value={`${formatDashboardNumber(data.llmCost.todayCalls)}회`}
          hint={`실패 ${formatDashboardNumber(data.llmCost.todayFailedCalls)}회`}
          tone="text-indigo-600"
          isLoading={isLoading}
        />
      </section>

      <section className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
        <Panel title="오늘 처리해야 할 업무" description="클릭하면 관련 관리 화면으로 이동합니다.">
          <div className="space-y-2">
            {data.todos.length === 0 ? (
              <EmptyState text="오늘 처리할 업무가 없습니다." />
            ) : (
              data.todos.map((todo) => (
                <Link
                  key={todo.type}
                  to={todo.targetPath}
                  className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm no-underline transition hover:border-[#315fbc] hover:bg-[#f5f8ff]"
                >
                  <span className="font-semibold text-slate-800">{todo.label}</span>
                  <span className="inline-flex items-center gap-2 font-bold text-slate-950">
                    {formatDashboardNumber(todo.count)}건
                    <ArrowRight className="h-4 w-4 text-slate-400" />
                  </span>
                </Link>
              ))
            )}
          </div>
        </Panel>

        <LlmCostPanel data={data} isLoading={isLoading} />
      </section>

      <section className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
        <Panel title="전체 면접 준비 진행률" description="상태값 기준 count입니다.">
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
        </Panel>

        <LlmTopNodesPanel data={data} isLoading={isLoading} />
      </section>

      <Panel title="검토 우선순위가 높은 지원자" description="실패, 일부 완료, 반려, 낮은 점수 기준으로 자동 산정합니다.">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[900px] border-separate border-spacing-y-2 text-left text-sm">
            <thead className="text-xs text-slate-500">
              <tr>
                <th className="px-3 py-2">우선순위</th>
                <th className="px-3 py-2">지원자</th>
                <th className="px-3 py-2">직무</th>
                <th className="px-3 py-2">현재 상태</th>
                <th className="px-3 py-2">사유</th>
                <th className="px-3 py-2">업데이트</th>
                <th className="px-3 py-2 text-right">액션</th>
              </tr>
            </thead>
            <tbody>
              {data.priorityCandidates.length === 0 ? (
                <tr>
                  <td colSpan={7}>
                    <EmptyState text="검토 우선순위 지원자가 없습니다." />
                  </td>
                </tr>
              ) : (
                data.priorityCandidates.map((candidate) => (
                  <tr key={`${candidate.candidateId}-${candidate.sessionId ?? "candidate"}-${candidate.status}`} className="bg-white">
                    <td className="rounded-l-lg border-y border-l border-slate-200 px-3 py-3">
                      <PriorityPill priority={candidate.priority} />
                    </td>
                    <td className="border-y border-slate-200 px-3 py-3 font-semibold text-slate-950">
                      {candidate.candidateName}
                    </td>
                    <td className="border-y border-slate-200 px-3 py-3 text-slate-600">
                      {candidate.targetJob ?? "-"}
                    </td>
                    <td className="border-y border-slate-200 px-3 py-3">
                      <StatusBadge status={candidate.status} />
                    </td>
                    <td className="border-y border-slate-200 px-3 py-3 text-slate-600">
                      {candidate.reason}
                    </td>
                    <td className="border-y border-slate-200 px-3 py-3 text-slate-500">
                      {formatDashboardDateTime(candidate.updatedAt)}
                    </td>
                    <td className="rounded-r-lg border-y border-r border-slate-200 px-3 py-3 text-right">
                      <Link
                        to={
                          candidate.sessionId
                            ? "/manager/interview-sessions"
                            : candidate.targetPath
                        }
                        state={sessionLinkState(candidate.sessionId)}
                        className="font-semibold text-[#315fbc] no-underline"
                      >
                        보기
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Panel>

      <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <Panel title="최근 생성된 면접 세션" description="면접 세션 생성일 기준 최신 목록입니다.">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] border-separate border-spacing-y-2 text-left text-sm">
              <thead className="text-xs text-slate-500">
                <tr>
                  <th className="px-3 py-2">세션</th>
                  <th className="px-3 py-2">지원자</th>
                  <th className="px-3 py-2">직무</th>
                  <th className="px-3 py-2">상태</th>
                  <th className="px-3 py-2 text-right">질문 수</th>
                </tr>
              </thead>
              <tbody>
                {data.recentSessions.map((session) => (
                  <tr key={session.sessionId} className="bg-white">
                    <td className="rounded-l-lg border-y border-l border-slate-200 px-3 py-3 font-semibold">
                      <Link
                        to="/manager/interview-sessions"
                        state={sessionLinkState(session.sessionId)}
                        className="text-slate-950 no-underline hover:text-[#315fbc]"
                      >
                        #{session.sessionId}
                      </Link>
                    </td>
                    <td className="border-y border-slate-200 px-3 py-3 text-slate-700">
                      {session.candidateName}
                    </td>
                    <td className="border-y border-slate-200 px-3 py-3 text-slate-600">
                      {session.targetJob}
                    </td>
                    <td className="border-y border-slate-200 px-3 py-3">
                      <StatusBadge status={session.status} />
                    </td>
                    <td className="rounded-r-lg border-y border-r border-slate-200 px-3 py-3 text-right font-semibold">
                      {formatDashboardNumber(session.questionCount)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title="최근 활동 로그" description="생성/요청/완료 시각을 합성한 업무 이벤트입니다.">
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
        </Panel>
      </section>
    </div>
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
  icon: typeof DollarSign;
  label: string;
  value: string;
  hint: string;
  tone: string;
  isLoading: boolean;
}) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <p className="m-0 text-sm font-semibold text-slate-500">{label}</p>
          <strong className="mt-2 block text-3xl font-bold text-slate-950">
            {isLoading ? "-" : value}
          </strong>
        </div>
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-50">
          <Icon className={`h-5 w-5 ${tone}`} />
        </div>
      </div>
      <p className="m-0 text-xs font-medium text-slate-500">{hint}</p>
    </article>
  );
}

function LlmCostPanel({
  data,
  isLoading,
}: {
  data: DashboardSummary;
  isLoading: boolean;
}) {
  const topNode = data.llmCost.topCostNode;

  return (
    <Panel title="AI 운영 비용" description="오늘 기준 LLM 호출과 월간 누적 비용입니다.">
      <div className="grid gap-3 sm:grid-cols-2">
        <CostStat
          label="오늘 비용"
          value={formatDashboardCurrency(data.llmCost.todayCost)}
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
        <CostStat
          label="평균 응답"
          value={formatDashboardSeconds(data.llmCost.avgElapsedMs)}
          isLoading={isLoading}
        />
      </div>

      <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="m-0 text-xs font-bold uppercase text-slate-500">
              가장 비용 높은 노드
            </p>
            <p className="m-0 mt-1 truncate text-sm font-bold text-slate-950">
              {topNode ? topNode.nodeName : "-"}
            </p>
          </div>
          <div className="text-right">
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
        AI 운영 현황 보기
        <ArrowRight className="h-4 w-4" />
      </Link>
    </Panel>
  );
}

function LlmTopNodesPanel({
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
    <Panel title="노드별 비용 Top 5" description="이번 달 비용 기준 LLM 노드 순위입니다.">
      <div className="space-y-3">
        {data.llmCost.topNodes.length === 0 ? (
          <EmptyState text="집계된 LLM 비용이 없습니다." />
        ) : (
          data.llmCost.topNodes.map((node) => (
            <div key={node.nodeName} className="space-y-1.5">
              <div className="flex items-center justify-between gap-3 text-sm">
                <span className="min-w-0 truncate font-semibold text-slate-700">
                  {node.nodeName}
                </span>
                <span className="shrink-0 font-bold text-slate-950">
                  {isLoading
                    ? "-"
                    : `${formatDashboardCurrency(node.estimatedCost)} · ${formatDashboardNumber(node.callCount)}회`}
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
    </Panel>
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

function getActivitySessionId(targetPath: string): number | null {
  const match = targetPath.match(/^\/manager\/interview-sessions\/(\d+)$/);
  if (!match) return null;
  const sessionId = Number(match[1]);
  return Number.isFinite(sessionId) ? sessionId : null;
}

function getActivityTargetPath(targetPath: string): string {
  return getActivitySessionId(targetPath) ? "/manager/interview-sessions" : targetPath;
}

function getActivityLinkState(targetPath: string) {
  const sessionId = getActivitySessionId(targetPath);
  return sessionId ? { openDetailSessionId: sessionId } : undefined;
}

function Panel({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-4">
        <h3 className="m-0 text-lg font-bold text-slate-950">{title}</h3>
        <p className="m-0 mt-1 text-sm text-slate-500">{description}</p>
      </div>
      {children}
    </section>
  );
}

function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${statusClasses(
        status,
      )}`}
    >
      {statusLabel(status)}
    </span>
  );
}

function PriorityPill({ priority }: { priority: DashboardPriority }) {
  return (
    <span
      className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${priorityClasses(
        priority,
      )}`}
    >
      {priorityLabel(priority)}
    </span>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 p-5 text-center text-sm text-slate-500">
      {text}
    </div>
  );
}
