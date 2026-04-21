import type { PagedListResponse } from "../../../../common/types/pagination";

export interface PromptProfileListRequest {
  page: number;
  limit: number;
  search?: string;
  targetJob?: string;
}

export interface PromptProfileResponse {
  id: number;
  profileKey: string;
  systemPrompt: string;
  outputSchema: string | null;
  targetJob: string | null;
  createdAt: string;
  createdBy: number | null;
  updatedAt: string;
  deletedAt: string | null;
  deletedBy: number | null;
}

export type PromptProfileListResponse = PagedListResponse<PromptProfileResponse>;

export interface PromptProfileCreateRequest {
  profileKey: string;
  systemPrompt: string;
  outputSchema?: string | null;
  targetJob?: string | null;
}

export interface PromptProfileUpdateRequest {
  systemPrompt: string;
  /** 수정 시 항상 전달. 빈 문자열이면 서버에서 null로 저장합니다. */
  outputSchema: string;
}

/** 신규 등록 시 에이전트 설정 + 수정 시 systemPrompt 편집에 공통 사용 */
export interface PromptProfileFormState {
  profileKey: string;
  systemPrompt: string;
  outputSchema: string;
  /** 1. 기본 정보 */
  agentName: string;
  department: string;
  jobTitle: string;
  /** 2. 기술 요건 — 칩 태그 (내부 값은 # 없이) */
  mustHaveStack: string[];
  niceToHaveStack: string[];
  requiredCertificates: string[];
  requiredEducation: string[];
}
