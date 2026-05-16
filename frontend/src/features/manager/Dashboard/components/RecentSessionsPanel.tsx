import { Link } from "react-router-dom";
import { formatDashboardNumber, type DashboardSummary } from "../types";
import { DashboardPanel, sessionLinkState, StatusBadge } from "./dashboardShared";

export function RecentSessionsPanel({ data }: { data: DashboardSummary }) {
  return (
    <DashboardPanel
      title="최근 생성된 면접 세션"
      description="면접 질문 준비 기준 최신 목록입니다."
    >
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
    </DashboardPanel>
  );
}
