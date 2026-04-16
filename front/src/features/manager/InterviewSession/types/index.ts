import type { PagedListResponse } from "../../../../common/types/pagination";

export interface InterviewSessionRequest {
  page: number;
  size: number;
  search?: string;
}

export interface InterviewSessionResponse {
  id: number;
  candidateName: string;
  targetJob: string;
  difficultyLevel: string;
  questionCount: number;
  status: string;
}

export type InterviewSessionListResponse =
  PagedListResponse<InterviewSessionResponse>;
