import type { PagedListResponse } from "../../../../common/types/pagination";
import type { CandidateJobPosition } from "../../Candidate/types";

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
  /** 지원 직무 enum; 생성 시 API `targetJob`에 그대로 저장 */
  targetJob: CandidateJobPosition | "";
  /** 2. 기술 요건 — 칩 태그 (내부 값은 # 없이) */
  mustHaveStack: string[];
  niceToHaveStack: string[];
  requiredCertificates: string[];
  requiredEducation: string[];
  /** 3. 부서 실무 상황 (생성 시 시스템 프롬프트에만 반영, 내부 맥락) */
  departmentReality: DepartmentRealityFormState;
}

export type DepartmentRealityQuestionId = "q1" | "q2" | "q3" | "q4";

export interface DepartmentRealityCustomItem {
  id: string;
  text: string;
}

export interface DepartmentRealityQuestionState {
  /** 프리셋 id(q1-…) 또는 커스텀 항목 id */
  selectedIds: string[];
  customItems: DepartmentRealityCustomItem[];
}

export type DepartmentRealityFormState = Record<
  DepartmentRealityQuestionId,
  DepartmentRealityQuestionState
>;
