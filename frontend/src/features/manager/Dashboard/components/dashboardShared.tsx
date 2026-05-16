import type { ReactNode } from "react";
import {
  priorityClasses,
  priorityLabel,
  riskClasses,
  riskLabel,
  statusClasses,
  statusLabel,
  type DashboardPriority,
} from "../types";

export function DashboardPanel({
  title,
  description,
  children,
  className = "",
}: {
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-lg border border-slate-200 bg-white p-4 shadow-sm ${className}`}>
      <div className="mb-4">
        <h3 className="m-0 text-base font-bold text-slate-950 sm:text-lg">{title}</h3>
        {description ? (
          <p className="m-0 mt-1 text-sm leading-5 text-slate-500">{description}</p>
        ) : null}
      </div>
      {children}
    </section>
  );
}

export function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 p-5 text-center text-sm text-slate-500">
      {text}
    </div>
  );
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${statusClasses(
        status,
      )}`}
    >
      {statusLabel(status)}
    </span>
  );
}

export function PriorityPill({ priority }: { priority: DashboardPriority }) {
  return (
    <span
      className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${priorityClasses(
        priority,
      )}`}
    >
      {priorityLabel(priority)}
    </span>
  );
}

export function RiskBadge({ riskLevel }: { riskLevel: string | null }) {
  return (
    <span
      className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${riskClasses(
        riskLevel,
      )}`}
    >
      {riskLabel(riskLevel)}
    </span>
  );
}

export function getActivitySessionId(targetPath: string): number | null {
  const match = targetPath.match(/^\/manager\/interview-sessions\/(\d+)$/);
  if (!match) return null;
  const sessionId = Number(match[1]);
  return Number.isFinite(sessionId) ? sessionId : null;
}

export function getActivityTargetPath(targetPath: string): string {
  return getActivitySessionId(targetPath) ? "/manager/interview-sessions" : targetPath;
}

export function getActivityLinkState(targetPath: string) {
  const sessionId = getActivitySessionId(targetPath);
  return sessionId ? { openDetailSessionId: sessionId } : undefined;
}

export function sessionLinkState(sessionId: number | null | undefined) {
  return sessionId ? { openDetailSessionId: sessionId } : undefined;
}

export function businessNodeLabel(nodeName: string): string {
  const labels: Record<string, string> = {
    reviewer: "질문 품질 검토",
    questioner: "면접 질문 생성",
    driller: "심화 질문 생성",
    jy_questioner: "직무 질문 생성",
    jy_driller: "직무 심화 질문",
    parser: "문서 구조화",
    retriever: "근거 검색",
    compliance_analyzer: "공고 리스크 분석",
    report_builder: "공고 리포트 작성",
  };
  return labels[nodeName] ?? nodeName.replaceAll("_", " ");
}
