import type { JobPostingAiJob } from "../types";

const terminalJobStatuses = new Set([
  "SUCCESS",
  "FAILED",
  "PARTIAL_SUCCESS",
  "CANCELLED",
]);

export function isTerminalJob(job: JobPostingAiJob) {
  return terminalJobStatuses.has(job.status);
}

export function jobStatusStyle(status: string) {
  const normalized = status.toUpperCase();
  if (normalized === "SUCCESS") return "border-emerald-200 bg-emerald-50 text-emerald-800";
  if (normalized === "FAILED" || normalized === "CANCELLED") {
    return "border-rose-200 bg-rose-50 text-rose-800";
  }
  if (normalized === "PARTIAL_SUCCESS") return "border-amber-200 bg-amber-50 text-amber-800";
  return "border-[#315fbc]/20 bg-[#edf4ff] text-[#173a7a]";
}
