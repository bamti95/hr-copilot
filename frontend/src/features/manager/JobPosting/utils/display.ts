import type {
  EvidenceSource,
  JobPostingAnalysisReport,
  JobPostingIssue,
} from "../types";

export const inputClassName =
  "h-11 w-full rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] px-4 text-sm text-[var(--text)] outline-none transition focus:border-[var(--primary)]";

export const textareaClassName =
  "min-h-[360px] w-full resize-y rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] px-4 py-3 text-sm leading-6 text-[var(--text)] outline-none transition focus:border-[var(--primary)]";

export function formatDateTime(value: string | null | undefined) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function riskStyle(level?: string | null) {
  const normalized = (level ?? "UNKNOWN").toUpperCase();
  if (normalized === "CRITICAL") return "border-rose-200 bg-rose-50 text-rose-700";
  if (normalized === "HIGH") return "border-orange-200 bg-orange-50 text-orange-700";
  if (normalized === "MEDIUM") return "border-amber-200 bg-amber-50 text-amber-700";
  if (normalized === "LOW") return "border-sky-200 bg-sky-50 text-sky-700";
  if (normalized === "CLEAN") return "border-emerald-200 bg-emerald-50 text-emerald-700";
  return "border-slate-200 bg-slate-50 text-slate-600";
}

export function toIssueList(
  value: JobPostingAnalysisReport["issueSummary"],
): JobPostingIssue[] {
  return Array.isArray(value) ? value : [];
}

export function toEvidenceList(
  value: JobPostingAnalysisReport["matchedEvidence"],
): EvidenceSource[] {
  return Array.isArray(value) ? value : [];
}
