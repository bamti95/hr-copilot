import { FileJson2 } from "lucide-react";
import { NodeTraceItem } from "./NodeTraceItem";
import type { LlmCallLog } from "../types/workflowDashboard.types";

interface NodeTraceTreeProps {
  logs: LlmCallLog[];
  traceId: string | null;
  selectedLogId: number | null;
  isLoading: boolean;
  error: string | null;
  onSelectLog: (logId: number) => void;
}

export function NodeTraceTree({
  logs,
  traceId,
  selectedLogId,
  isLoading,
  error,
  onSelectLog,
}: NodeTraceTreeProps) {
  return (
    <div className="flex min-h-[860px] min-w-0 flex-col rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="m-0 truncate text-lg font-bold text-slate-950">
            노드 추적 트리
          </h2>
          <p className="m-0 mt-1 truncate text-xs text-slate-500">
            {traceId ? `추적 ID ${traceId.slice(0, 8)}` : "추적 ID 없음"}
          </p>
        </div>
        <FileJson2 className="h-5 w-5 shrink-0 text-[#315fbc]" />
      </div>

      {error ? (
        <div className="mb-3 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          {error}
        </div>
      ) : null}

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 8 }).map((_, index) => (
            <div key={index} className="h-10 animate-pulse rounded-lg bg-slate-100" />
          ))}
        </div>
      ) : logs.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 p-5 text-center text-sm text-slate-500">
          세션을 선택하면 노드 실행 로그가 표시됩니다.
        </div>
      ) : (
        <div className="min-h-0 flex-1 overflow-auto rounded-lg border border-slate-200 bg-slate-50 p-2">
          <div className="mb-2 px-2 py-1 text-xs font-bold uppercase text-slate-500">
            LangGraph
          </div>
          {logs.map((log, index) => (
            <NodeTraceItem
              key={log.id}
              log={log}
              isLast={index === logs.length - 1}
              isSelected={selectedLogId === log.id}
              onSelect={onSelectLog}
            />
          ))}
        </div>
      )}
    </div>
  );
}
