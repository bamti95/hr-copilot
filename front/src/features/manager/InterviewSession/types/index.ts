import type { PagedListResponse } from "../../../../common/types/pagination";

export type InterviewDifficultyLevel = "JUNIOR" | "INTERMEDIATE" | "SENIOR";

export interface InterviewSessionListRequest {
  page: number;
  limit: number;
  candidateId?: number;
  targetJob?: string;
}

export interface InterviewSessionCreateRequest {
  candidateId: number;
  targetJob: string;
  difficultyLevel?: string | null;
}

export interface InterviewSessionUpdateRequest {
  targetJob: string;
  difficultyLevel?: string | null;
}

export interface InterviewSessionFormState {
  candidateId: string;
  targetJob: string;
  difficultyLevel: string;
}

export interface InterviewSessionResponse {
  id: number;
  candidateId: number;
  candidateName: string;
  targetJob: string;
  difficultyLevel: string | null;
  createdAt: string;
  createdBy: number | null;
  deletedAt: string | null;
  deletedBy: number | null;
}

export interface InterviewSessionCandidateOption {
  id: number;
  name: string;
  email: string;
}

export type InterviewSessionListResponse =
  PagedListResponse<InterviewSessionResponse>;
