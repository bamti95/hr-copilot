import { useEffect, useMemo, useState } from "react";
import { NodeDetailPanel } from "../components/NodeDetailPanel";
import { NodeTraceTree } from "../components/NodeTraceTree";
import { QuestionResultPanel } from "../components/QuestionResultPanel";
import { RouterHistoryPanel } from "../components/RouterHistoryPanel";
import { ScoreBreakdownPanel } from "../components/ScoreBreakdownPanel";
import { SessionListPanel } from "../components/SessionListPanel";
import { WorkflowChartSection } from "../components/WorkflowChartSection";
import { WorkflowSummaryCards } from "../components/WorkflowSummaryCards";
import { useSelectedNodeLog } from "../hooks/useSelectedNodeLog";
import { useSessionLlmLogs } from "../hooks/useSessionLlmLogs";
import { useWorkflowSessions } from "../hooks/useWorkflowSessions";
import {
  emptyWorkflowSummary,
  getFinalResponse,
  getWorkflowExecutionId,
  workflowPipelineOptions,
  type WorkflowPipelineType,
} from "../types/workflowDashboard.types";

export default function WorkflowDashboardPage() {
  const [activePipeline, setActivePipeline] =
    useState<WorkflowPipelineType>("INTERVIEW_QUESTION");
  const { data, isLoading, error, reload } = useWorkflowSessions(activePipeline);
  const { workflowLogs, isTraceLoading, traceError, loadSessionLogs } =
    useSessionLlmLogs();
  const summary = data ?? emptyWorkflowSummary;
  const activeWorkflowLogs = workflowLogs;
  const logs = activeWorkflowLogs?.items ?? [];
  const {
    selectedLog,
    activeTab,
    setActiveTab,
    selectLog,
    resetSelectedLog,
  } = useSelectedNodeLog(logs);
  const [selectedSessionId, setSelectedSessionId] = useState<number | null>(null);

  useEffect(() => {
    resetSelectedLog();
    const firstSessionId = summary.bySession[0]
      ? getWorkflowExecutionId(summary.bySession[0])
      : null;
    setSelectedSessionId(firstSessionId);
    if (firstSessionId) {
      void loadSessionLogs(firstSessionId, activePipeline);
    }
  }, [activePipeline, loadSessionLogs, summary.bySession]);

  const totalSessionCost = useMemo(
    () =>
      summary.bySession.reduce(
        (sum, session) => sum + session.estimatedCost,
        0,
      ),
    [summary.bySession],
  );
  const finalResponse = getFinalResponse(logs);

  function handleSelectSession(sessionId: number) {
    setSelectedSessionId(sessionId);
    resetSelectedLog();
    void loadSessionLogs(sessionId, activePipeline);
  }

  return (
    <div className="flex min-w-0 flex-col gap-5">
      <section className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
        <div className="flex flex-wrap gap-2">
          {workflowPipelineOptions.map((option) => {
            const active = option.value === activePipeline;
            return (
              <button
                key={option.value}
                type="button"
                onClick={() => setActivePipeline(option.value)}
                className={`min-w-[180px] rounded-lg border px-4 py-3 text-left transition ${
                  active
                    ? "border-[#315fbc] bg-[#edf4ff] text-[#173a7a]"
                    : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                }`}
              >
                <div className="text-sm font-bold">{option.label}</div>
                <div className="mt-1 text-xs">{option.description}</div>
              </button>
            );
          })}
        </div>
      </section>
      <WorkflowSummaryCards
        metrics={summary.metrics}
        totalSessions={summary.bySession.length}
        totalSessionCost={totalSessionCost}
      />
      <WorkflowChartSection
        metrics={summary.metrics}
        byNode={summary.byNode}
        bySession={summary.bySession}
        isLoading={isLoading}
        error={error}
        onRefresh={() => {
          void reload();
        }}
      />
      <section className="grid min-h-[860px] gap-4 xl:grid-cols-[1.15fr_0.85fr_1.45fr]">
        <SessionListPanel
          pipelineType={activePipeline}
          sessions={summary.bySession}
          recentCalls={summary.recentCalls}
          activeSessionId={activeWorkflowLogs?.sessionId ?? selectedSessionId}
          onSelectSession={handleSelectSession}
        />
        <NodeTraceTree
          logs={logs}
          traceId={activeWorkflowLogs?.traceId ?? null}
          selectedLogId={selectedLog?.id ?? null}
          isLoading={isTraceLoading}
          error={traceError}
          onSelectLog={selectLog}
        />
        <NodeDetailPanel
          log={selectedLog}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />
      </section>
      <section className="grid gap-4 xl:grid-cols-[1.3fr_0.8fr_0.9fr]">
        <QuestionResultPanel finalResponse={finalResponse} />
        <ScoreBreakdownPanel logs={logs} finalResponse={finalResponse} />
        <RouterHistoryPanel logs={logs} />
      </section>
    </div>
  );
}
