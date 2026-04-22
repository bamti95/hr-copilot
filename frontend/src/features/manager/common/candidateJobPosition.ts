import type { CandidateJobPosition } from "../Candidate/types";

export const JOB_POSITION_LABEL: Record<CandidateJobPosition, string> = {
  STRATEGY_PLANNING: "기획·전략",
  HR: "인사·HR",
  MARKETING: "마케팅·광고·MD",
  AI_DEV_DATA: "AI·개발·데이터",
  SALES: "영업",
};

const ORDER: CandidateJobPosition[] = [
  "STRATEGY_PLANNING",
  "HR",
  "MARKETING",
  "AI_DEV_DATA",
  "SALES",
];

export const CANDIDATE_JOB_POSITION_OPTIONS: Array<{
  value: CandidateJobPosition;
  label: string;
}> = ORDER.map((value) => ({
  value,
  label: JOB_POSITION_LABEL[value],
}));

export function getJobPositionLabel(jobPosition: string): string {
  return JOB_POSITION_LABEL[jobPosition as CandidateJobPosition] ?? jobPosition;
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
