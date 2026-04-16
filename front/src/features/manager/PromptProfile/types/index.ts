import type { PagedListResponse } from "../../../../common/types/pagination";

export interface PromptProfileRequest {
  page: number;
  size: number;
  search?: string;
}

export interface PromptProfileResponse {
  id: number;
  profileKey: string;
  persona: string;
  outputSchema: string;
  status: string;
}

export type PromptProfileListResponse = PagedListResponse<PromptProfileResponse>;
