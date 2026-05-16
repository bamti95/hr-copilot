import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { formatDashboardNumber, type DashboardSummary } from "../types";
import { DashboardPanel, EmptyState } from "./dashboardShared";

export function TodayWorkPanel({ data }: { data: DashboardSummary }) {
  const jobPostingTasks = [
    {
      type: "JOB_POSTING_PENDING",
      label: "채용공고 분석 진행 중",
      count: data.jobPosting.pendingAnalysisCount,
      targetPath: "/manager/job-postings",
    },
    {
      type: "JOB_POSTING_FAILED",
      label: "채용공고 분석 실패",
      count: data.jobPosting.failedAnalysisCount,
      targetPath: "/manager/job-postings",
    },
    {
      type: "JOB_POSTING_REVIEW_REQUIRED",
      label: "공고 문구 검토 필요",
      count: data.jobPosting.reviewRequiredCount,
      targetPath: "/manager/job-postings",
    },
  ].filter((item) => item.count > 0);

  const items = [...data.todos, ...jobPostingTasks];

  return (
    <DashboardPanel
      title="오늘 처리해야 할 업무"
      description="클릭하면 관련 관리 화면으로 이동합니다."
    >
      <div className="space-y-2">
        {items.length === 0 ? (
          <EmptyState text="오늘 바로 처리할 업무가 없습니다." />
        ) : (
          items.map((todo) => (
            <Link
              key={todo.type}
              to={todo.targetPath}
              className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm no-underline transition hover:border-[#315fbc] hover:bg-[#f5f8ff]"
            >
              <span className="min-w-0 font-semibold text-slate-800">{todo.label}</span>
              <span className="inline-flex shrink-0 items-center gap-2 font-bold text-slate-950">
                {formatDashboardNumber(todo.count)}건
                <ArrowRight className="h-4 w-4 text-slate-400" />
              </span>
            </Link>
          ))
        )}
      </div>
    </DashboardPanel>
  );
}
