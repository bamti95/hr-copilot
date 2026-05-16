import { Link } from "react-router-dom";
import { ArrowRight, FileSearch } from "lucide-react";
import {
  formatDashboardCurrency,
  formatDashboardDateTime,
  formatDashboardNumber,
  type DashboardSummary,
} from "../types";
import { DashboardPanel, EmptyState, RiskBadge, StatusBadge } from "./dashboardShared";

export function JobPostingRagPanel({
  data,
  isLoading,
}: {
  data: DashboardSummary;
  isLoading: boolean;
}) {
  const summary = data.jobPosting;
  const knowledgeReadyRatio =
    summary.knowledgeSourcesCount > 0
      ? Math.round(
          (summary.indexedKnowledgeSourcesCount / summary.knowledgeSourcesCount) * 100,
        )
      : 0;

  return (
    <DashboardPanel
      title="채용공고 RAG 분석"
      description="공고 문구의 법률 리스크, 근거 검색 준비 상태, 예상 분석 비용입니다."
      className="xl:col-span-2"
    >
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <RagStat
          label="분석 완료 공고"
          value={`${formatDashboardNumber(summary.analyzedCount)}건`}
          subValue={`전체 ${formatDashboardNumber(summary.totalPostings)}건`}
          isLoading={isLoading}
        />
        <RagStat
          label="검토 필요한 공고"
          value={`${formatDashboardNumber(summary.reviewRequiredCount)}건`}
          subValue={`실패 ${formatDashboardNumber(summary.failedAnalysisCount)}건`}
          isLoading={isLoading}
        />
        <RagStat
          label="근거 지식 색인"
          value={`${formatDashboardNumber(summary.indexedKnowledgeSourcesCount)}개`}
          subValue={`준비율 ${knowledgeReadyRatio}%`}
          isLoading={isLoading}
        />
        <RagStat
          label="공고 1건 예상 비용"
          value={formatDashboardCurrency(summary.estimatedNextAnalysisCost)}
          subValue={`오늘 예상 ${formatDashboardCurrency(summary.projectedTodayCost)}`}
          isLoading={isLoading}
        />
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-white">
              <FileSearch className="h-5 w-5 text-[#315fbc]" />
            </div>
            <div className="min-w-0">
              <p className="m-0 text-sm font-bold text-slate-950">
                오늘 공고 분석 비용
              </p>
              <p className="m-0 mt-1 text-2xl font-bold text-slate-950">
                {isLoading ? "-" : formatDashboardCurrency(summary.todayCost)}
              </p>
              <p className="m-0 mt-1 text-xs font-semibold text-slate-500">
                이번 달 누적 {formatDashboardCurrency(summary.monthCost)}
              </p>
            </div>
          </div>
          <Link
            to="/manager/job-postings/new"
            className="mt-4 inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-[#315fbc] bg-white px-3 text-sm font-bold text-[#315fbc] no-underline transition hover:bg-[#f5f8ff]"
          >
            새 공고 분석
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        <div className="space-y-2">
          {summary.recentReports.length === 0 ? (
            <EmptyState text="최근 채용공고 분석 리포트가 없습니다." />
          ) : (
            summary.recentReports.slice(0, 4).map((report) => (
              <Link
                key={report.reportId}
                to={report.targetPath}
                className="grid gap-3 rounded-lg border border-slate-200 bg-white p-3 text-sm no-underline transition hover:border-[#315fbc] hover:bg-[#f5f8ff] sm:grid-cols-[1fr_auto]"
              >
                <div className="min-w-0">
                  <p className="m-0 truncate font-bold text-slate-950">
                    {report.jobTitle}
                  </p>
                  <p className="m-0 mt-1 truncate text-xs text-slate-500">
                    {report.companyName ?? "회사명 미입력"} · 이슈{" "}
                    {formatDashboardNumber(report.issueCount)}건
                  </p>
                </div>
                <div className="flex items-center gap-2 sm:justify-end">
                  <RiskBadge riskLevel={report.riskLevel} />
                  <StatusBadge status={report.status} />
                  <span className="hidden text-xs font-semibold text-slate-400 md:inline">
                    {formatDashboardDateTime(report.updatedAt)}
                  </span>
                </div>
              </Link>
            ))
          )}
        </div>
      </div>
    </DashboardPanel>
  );
}

function RagStat({
  label,
  value,
  subValue,
  isLoading,
}: {
  label: string;
  value: string;
  subValue: string;
  isLoading: boolean;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-4 py-3">
      <p className="m-0 text-xs font-semibold text-slate-500">{label}</p>
      <p className="m-0 mt-1 text-lg font-bold text-slate-950">
        {isLoading ? "-" : value}
      </p>
      <p className="m-0 mt-1 text-xs font-semibold text-slate-500">{subValue}</p>
    </div>
  );
}
