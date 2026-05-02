import { useMemo, useState } from "react";
import type { DetailTab, LlmCallLog } from "../types/workflowDashboard.types";

export function useSelectedNodeLog(logs: LlmCallLog[]) {
  const [selectedLogId, setSelectedLogId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<DetailTab>("feedback");

  const selectedLog = useMemo(
    () => logs.find((log) => log.id === selectedLogId) ?? logs[0] ?? null,
    [logs, selectedLogId],
  );

  function selectLog(logId: number) {
    setSelectedLogId(logId);
    setActiveTab("feedback");
  }

  function resetSelectedLog() {
    setSelectedLogId(null);
    setActiveTab("feedback");
  }

  return {
    selectedLog,
    activeTab,
    setActiveTab,
    selectLog,
    resetSelectedLog,
  };
}
