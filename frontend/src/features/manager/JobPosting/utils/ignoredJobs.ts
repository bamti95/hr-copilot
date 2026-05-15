const MAX_IGNORED_JOB_IDS = 20;

function readIgnoredJobIds(storageKey: string): number[] {
  try {
    const raw = window.localStorage.getItem(storageKey);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed)
      ? parsed.map(Number).filter((value) => Number.isFinite(value))
      : [];
  } catch {
    return [];
  }
}

export function isIgnoredJobId(storageKey: string, jobId: number | null | undefined) {
  if (!jobId) return false;
  return readIgnoredJobIds(storageKey).includes(jobId);
}

export function rememberIgnoredJobId(storageKey: string, jobId: number | null | undefined) {
  if (!jobId) return;
  try {
    const nextIds = [
      jobId,
      ...readIgnoredJobIds(storageKey).filter((storedJobId) => storedJobId !== jobId),
    ].slice(0, MAX_IGNORED_JOB_IDS);
    window.localStorage.setItem(storageKey, JSON.stringify(nextIds));
  } catch {
    // Best-effort UI polling suppression only.
  }
}

export function forgetIgnoredJobId(storageKey: string, jobId: number | null | undefined) {
  if (!jobId) return;
  try {
    const nextIds = readIgnoredJobIds(storageKey).filter(
      (storedJobId) => storedJobId !== jobId,
    );
    window.localStorage.setItem(storageKey, JSON.stringify(nextIds));
  } catch {
    // Best-effort UI polling suppression only.
  }
}
