import type { JobPostingAiJob } from "../types";
import { isTerminalJob } from "./jobStatus";

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export async function pollJob(
  initialJob: JobPostingAiJob,
  fetcher: (jobId: number) => Promise<JobPostingAiJob>,
  onUpdate: (job: JobPostingAiJob) => void,
): Promise<JobPostingAiJob> {
  let current = initialJob;
  onUpdate(current);
  for (let attempt = 0; attempt < 240; attempt += 1) {
    if (isTerminalJob(current)) return current;
    await sleep(1500);
    current = await fetcher(current.jobId);
    onUpdate(current);
  }
  throw new Error("작업 상태 확인 시간이 초과되었습니다.");
}
