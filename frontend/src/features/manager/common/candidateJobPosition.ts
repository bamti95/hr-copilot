export const JOB_POSITION_LABEL: Record<string, string> = {
  STRATEGY_PLANNING: "기획·전략",
  HR: "인사·HR",
  MARKETING: "마케팅·광고·MD",
  AI_DEV_DATA: "AI·개발·데이터",
  SALES: "영업",
};

const ORDER = [
  "STRATEGY_PLANNING",
  "HR",
  "MARKETING",
  "AI_DEV_DATA",
  "SALES",
] as const;

type CandidateJobPosition = (typeof ORDER)[number];

export const CANDIDATE_JOB_POSITION_OPTIONS: Array<{
  value: string;
  label: string;
}> = ORDER.map((value) => ({
  value,
  label: JOB_POSITION_LABEL[value],
}));

export function getJobPositionLabel(jobPosition: string): string {
  const trimmed = jobPosition.trim();
  const suffixMatch = trimmed.match(/\s*(\((?:신입|경력)\))$/);
  const suffix = suffixMatch?.[1] ?? "";
  const basePosition = suffix ? trimmed.slice(0, -suffix.length).trim() : trimmed;
  const label = JOB_POSITION_LABEL[basePosition as CandidateJobPosition] ?? basePosition;

  return suffix ? `${label} ${suffix}` : label;
}

export function getJobAliasesForMatch(targetJob: string): Set<string> {
  const trimmed = targetJob.trim();
  const koreanLabel = JOB_POSITION_LABEL[trimmed as CandidateJobPosition];

  return new Set(
    [trimmed, koreanLabel]
      .filter((value): value is string => Boolean(value))
      .map((value) => value.toLowerCase()),
  );
}

export interface PromptProfileJobMatchTarget {
  targetJob: string | null;
}

export function isMatchingPromptProfile(
  profile: PromptProfileJobMatchTarget,
  targetJob: string,
): boolean {
  if (!profile.targetJob) {
    return false;
  }

  const aliases = getJobAliasesForMatch(targetJob);
  return aliases.has(profile.targetJob.trim().toLowerCase());
}
