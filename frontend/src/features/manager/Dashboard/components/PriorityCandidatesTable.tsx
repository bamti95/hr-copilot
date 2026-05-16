import { Link } from "react-router-dom";
import {
  formatDashboardDateTime,
  type DashboardSummary,
} from "../types";
import {
  DashboardPanel,
  EmptyState,
  PriorityPill,
  sessionLinkState,
  StatusBadge,
} from "./dashboardShared";

export function PriorityCandidatesTable({ data }: { data: DashboardSummary }) {
  return (
    <DashboardPanel
      title="검토 우선순위가 높은 지원자"
      description="실패, 일부 완료, 반려, 낮은 점수 기준으로 자동 선정합니다."
    >
      <div className="overflow-x-auto">
        <table className="w-full min-w-[860px] border-separate border-spacing-y-2 text-left text-sm">
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
                <tr
                  key={`${candidate.candidateId}-${candidate.sessionId ?? "candidate"}-${candidate.status}`}
                  className="bg-white"
                >
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
    </DashboardPanel>
  );
}
