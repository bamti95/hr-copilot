import { BottomPanel, EmptyState } from "./QuestionResultPanel";
import { formatMs, type LlmCallLog } from "../types/workflowDashboard.types";

interface RouterHistoryPanelProps {
  logs: LlmCallLog[];
}

export function RouterHistoryPanel({ logs }: RouterHistoryPanelProps) {
  const routerLogs = logs.filter((log) => {
    const name = log.nodeName ?? "";
    return name.includes("route") || name.includes("retry");
  });

  return (
    <BottomPanel title="라우터 이력">
      <div className="space-y-2">
        {routerLogs.map((log) => (
          <article
            key={log.id}
            className="rounded-lg border border-slate-200 bg-white p-3 text-sm"
          >
            <div className="font-semibold text-slate-900">{log.nodeName}</div>
            <div className="mt-1 text-xs text-slate-500">
              실행 순서 {log.executionOrder ?? "-"} / {formatMs(log.elapsedMs)}
            </div>
          </article>
        ))}
        {routerLogs.length === 0 ? (
          <EmptyState text="라우터 분기 사유는 outputJson.router 또는 responseJson.router에 저장되면 표시할 수 있습니다." />
        ) : null}
      </div>
    </BottomPanel>
  );
}
