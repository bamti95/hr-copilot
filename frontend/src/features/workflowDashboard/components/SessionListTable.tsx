import {
  formatCost,
  formatDateTime,
  formatMs,
  getCallExecutionId,
  getWorkflowExecutionId,
  getWorkflowExecutionSubtitle,
  getWorkflowExecutionTitle,
  normalizeStatus,
  statusClasses,
  statusLabel,
  type LlmUsageCallLog,
  type LlmUsageSessionSummary,
  type WorkflowPipelineType,
} from "../types/workflowDashboard.types";

interface SessionListTableProps {
  pipelineType: WorkflowPipelineType;
  sessions: LlmUsageSessionSummary[];
  recentCalls: LlmUsageCallLog[];
  activeSessionId: number | null;
  onSelectSession: (sessionId: number) => void;
}

export function SessionListTable({
  pipelineType,
  sessions,
  recentCalls,
  activeSessionId,
  onSelectSession,
}: SessionListTableProps) {
  const isJobPosting = pipelineType === "JOB_POSTING_COMPLIANCE";

  if (sessions.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 p-5 text-center text-sm text-slate-500">
        표시할 실행 목록이 없습니다.
      </div>
    );
  }

  return (
    <div className="min-h-0 flex-1 overflow-auto">
      <table className="w-full min-w-[720px] border-separate border-spacing-y-2 text-left text-xs">
        <thead className="sticky top-0 bg-white text-slate-500">
          <tr>
            <th className="px-2 py-2">상태</th>
            <th className="px-2 py-2">
              {isJobPosting ? "분석 리포트" : "지원자"}
            </th>
            <th className="px-2 py-2">
              {isJobPosting ? "위험등급" : "직무"}
            </th>
            <th className="px-2 py-2 text-right">실행시간</th>
            <th className="px-2 py-2 text-right">비용</th>
            <th className="px-2 py-2">실행일시</th>
          </tr>
        </thead>
        <tbody>
          {sessions.map((session) => {
            const executionId = getWorkflowExecutionId(session);
            const sessionCalls = recentCalls.filter(
              (call) => getCallExecutionId(call) === executionId,
            );
            const hasFailure = sessionCalls.some(
              (call) => normalizeStatus(call.callStatus) === "failed",
            );
            const status = hasFailure ? "failed" : "success";
            const active = activeSessionId === executionId;

            return (
              <tr
                key={executionId ?? `${session.jobTitle}-${session.lastCalledAt}`}
                onClick={() => {
                  if (executionId !== null) onSelectSession(executionId);
                }}
                className={`cursor-pointer bg-white transition hover:bg-[#f5f8ff] ${
                  active ? "outline outline-2 outline-[#315fbc]/30" : ""
                }`}
              >
                <td className="rounded-l-lg border-y border-l border-slate-200 px-2 py-3">
                  <span
                    className={`inline-flex rounded-full border px-2 py-1 text-[11px] font-semibold ${statusClasses(
                      status,
                    )}`}
                  >
                    {statusLabel(status)}
                  </span>
                </td>
                <td className="border-y border-slate-200 px-2 py-3">
                  <div className="font-semibold text-slate-900">
                    {getWorkflowExecutionTitle(session)}
                  </div>
                  <div className="text-slate-500">
                    {isJobPosting ? "리포트" : "세션"} #{executionId ?? "-"}
                  </div>
                </td>
                <td className="border-y border-slate-200 px-2 py-3">
                  {getWorkflowExecutionSubtitle(session)}
                </td>
                <td className="border-y border-slate-200 px-2 py-3 text-right">
                  {formatMs(session.avgElapsedMs)}
                </td>
                <td className="border-y border-slate-200 px-2 py-3 text-right">
                  {formatCost(session.estimatedCost)}
                </td>
                <td className="rounded-r-lg border-y border-r border-slate-200 px-2 py-3">
                  {formatDateTime(session.lastCalledAt)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
