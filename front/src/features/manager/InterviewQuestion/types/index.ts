import type { PagedListResponse } from "../../../../common/types/pagination";

export interface InterviewQuestionRequest {
  page: number;
  size: number;
  search?: string;
}

export interface InterviewQuestionResponse {
  id: number;
  category: string;
  questionText: string;
  expectedAnswer: string;
  priority: string;
}

export type InterviewQuestionListResponse =
  PagedListResponse<InterviewQuestionResponse>;
