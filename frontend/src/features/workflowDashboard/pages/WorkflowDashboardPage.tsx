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
} from "../types/workflowDashboard.types";

export default function WorkflowDashboardPage() {
  const { data, isLoading, error, reload } = useWorkflowSessions();
  const { workflowLogs, isTraceLoading, traceError, loadSessionLogs } =
    useSessionLlmLogs();
  const summary = data ?? emptyWorkflowSummary;
  const logs = workflowLogs?.items ?? [];
  const {
    selectedLog,
    activeTab,
    setActiveTab,
    selectLog,
    resetSelectedLog,
  } = useSelectedNodeLog(logs);
  const [selectedSessionId, setSelectedSessionId] = useState<number | null>(null);

  useEffect(() => {
    const firstSessionId = summary.bySession[0]?.sessionId;
    if (!selectedSessionId && firstSessionId) {
      setSelectedSessionId(firstSessionId);
      void loadSessionLogs(firstSessionId);
    }
  }, [loadSessionLogs, selectedSessionId, summary.bySession]);

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
    void loadSessionLogs(sessionId);
  }

  return (
    <div className="flex min-w-0 flex-col gap-5">
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
      <section className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr_1.35fr]">
        <SessionListPanel
          sessions={summary.bySession}
          recentCalls={summary.recentCalls}
          activeSessionId={workflowLogs?.sessionId ?? selectedSessionId}
          onSelectSession={handleSelectSession}
        />
        <NodeTraceTree
          logs={logs}
          traceId={workflowLogs?.traceId ?? null}
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
