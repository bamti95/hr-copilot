import type { JobPostingAiJob } from "../types";
import { jobStatusStyle } from "../utils/jobStatus";

interface JobProgressCardProps {
  job: JobPostingAiJob;
  onCancelJob?: () => void;
  cancelLabel?: string;
}

export function JobProgressCard({
  job,
  onCancelJob,
  cancelLabel = "작업 취소",
}: JobProgressCardProps) {
  return (
    <div className={`rounded-2xl border px-4 py-3 text-sm ${jobStatusStyle(job.status)}`}>
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="font-bold">
            Job #{job.jobId} · {job.status}
          </div>
          <div className="mt-1 text-xs opacity-80">
            {job.currentStep ?? job.message}
          </div>
          {onCancelJob ? (
            <button
              type="button"
              onClick={onCancelJob}
              className="mt-2 rounded-lg border border-current/25 bg-white/60 px-2.5 py-1 text-xs font-semibold transition hover:bg-white"
            >
              {cancelLabel}
            </button>
          ) : null}
        </div>
        <div className="min-w-45">
          <div className="flex items-center justify-between text-xs font-semibold">
            <span>진행률</span>
            <span>{job.progress}%</span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/70">
            <div
              className="h-full rounded-full bg-current transition-all"
              style={{ width: `${Math.max(0, Math.min(job.progress, 100))}%` }}
            />
          </div>
        </div>
      </div>
      {job.errorMessage ? (
        <div className="mt-3 rounded-xl bg-white/70 px-3 py-2 text-xs">
          {job.errorMessage}
        </div>
      ) : null}
    </div>
  );
}
