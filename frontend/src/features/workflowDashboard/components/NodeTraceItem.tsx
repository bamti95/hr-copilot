import { CheckCircle2, XCircle } from "lucide-react";
import {
  formatMs,
  normalizeStatus,
  type LlmCallLog,
} from "../types/workflowDashboard.types";

interface NodeTraceItemProps {
  log: LlmCallLog;
  isLast: boolean;
  isSelected: boolean;
  onSelect: (logId: number) => void;
}

export function NodeTraceItem({
  log,
  isLast,
  isSelected,
  onSelect,
}: NodeTraceItemProps) {
  const nodeName = log.nodeName ?? "unknown";
  const retrySuffix =
    nodeName.includes("retry") || (log.executionOrder ?? 0) > 8 ? " 재시도 경로" : "";

  return (
    <button
      type="button"
      onClick={() => onSelect(log.id)}
      className={`mb-1 flex w-full min-w-0 items-center gap-2 rounded-lg border px-2 py-2 text-left text-sm transition ${
        isSelected
          ? "border-[#315fbc]/40 bg-white text-[#1f4fbd]"
          : "border-transparent bg-transparent text-slate-700 hover:bg-white"
      }`}
    >
      <span className="w-5 shrink-0 font-mono text-xs text-slate-400">
        {isLast ? "`-" : "|-"}
      </span>
      {normalizeStatus(log.callStatus) === "failed" ? (
        <XCircle className="h-4 w-4 shrink-0 text-rose-500" />
      ) : (
        <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-500" />
      )}
      <span className="min-w-0 flex-1 truncate font-semibold">
        {nodeName}
        {retrySuffix}
      </span>
      <span className="shrink-0 text-xs text-slate-500">{formatMs(log.elapsedMs)}</span>
    </button>
  );
}

