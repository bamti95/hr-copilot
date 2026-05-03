import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import { SessionListTable } from "./SessionListTable";
import {
  normalizeStatus,
  type LlmUsageCallLog,
  type LlmUsageSessionSummary,
  type SessionFilter,
  type SessionSort,
} from "../types/workflowDashboard.types";

interface SessionListPanelProps {
  sessions: LlmUsageSessionSummary[];
  recentCalls: LlmUsageCallLog[];
  activeSessionId: number | null;
  onSelectSession: (sessionId: number) => void;
}

export function SessionListPanel({
  sessions,
  recentCalls,
  activeSessionId,
  onSelectSession,
}: SessionListPanelProps) {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<SessionFilter>("all");
  const [sort, setSort] = useState<SessionSort>("recent");

  const filteredSessions = useMemo(() => {
    const query = search.trim().toLowerCase();
    const rows = sessions.filter((session) => {
      const sessionCalls = recentCalls.filter(
        (call) => call.sessionId === session.sessionId,
      );
      const hasFailure = sessionCalls.some(
        (call) => normalizeStatus(call.callStatus) === "failed",
      );
      if (filter === "success" && hasFailure) return false;
      if (filter === "failed" && !hasFailure) return false;
      if (!query) return true;
      return `${session.candidateName} ${session.targetJob} ${session.sessionId}`
        .toLowerCase()
        .includes(query);
    });

    return [...rows].sort((a, b) => {
      if (sort === "latency") return b.avgElapsedMs - a.avgElapsedMs;
      if (sort === "cost") return b.estimatedCost - a.estimatedCost;
      if (sort === "tokens") return b.totalTokens - a.totalTokens;
      return (
        new Date(b.lastCalledAt ?? 0).getTime() -
        new Date(a.lastCalledAt ?? 0).getTime()
      );
    });
  }, [filter, recentCalls, search, sessions, sort]);

  return (
    <div className="flex min-h-[860px] min-w-0 flex-col rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3">
        <h2 className="m-0 text-lg font-bold text-slate-950">지원자 세션 목록</h2>
        <p className="m-0 mt-1 text-xs text-slate-500">LangSmith 실행 목록 역할</p>
      </div>
      <div className="mb-3 grid gap-2 md:grid-cols-[1fr_auto_auto]">
        <label className="relative block">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            className="h-10 w-full rounded-lg border border-slate-200 bg-white pl-9 pr-3 text-sm outline-none focus:border-[#315fbc]"
            placeholder="지원자명, 직무, 세션 검색"
          />
        </label>
        <select
          value={filter}
          onChange={(event) => setFilter(event.target.value as SessionFilter)}
          className="h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm"
        >
          <option value="all">전체</option>
          <option value="success">성공</option>
          <option value="failed">실패</option>
        </select>
        <select
          value={sort}
          onChange={(event) => setSort(event.target.value as SessionSort)}
          className="h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm"
        >
          <option value="recent">최근순</option>
          <option value="latency">실행시간순</option>
          <option value="cost">비용순</option>
          <option value="tokens">토큰순</option>
        </select>
      </div>

      <SessionListTable
        sessions={filteredSessions}
        recentCalls={recentCalls}
        activeSessionId={activeSessionId}
        onSelectSession={onSelectSession}
      />
    </div>
  );
}
