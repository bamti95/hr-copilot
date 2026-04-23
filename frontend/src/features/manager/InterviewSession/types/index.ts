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
  promptProfileId: number;
}

export interface InterviewSessionUpdateRequest {
  targetJob: string;
  difficultyLevel?: string | null;
}

export interface InterviewSessionFormState {
  candidateId: string;
  targetJob: string;
  difficultyLevel: string;
  promptProfileId: string;
}

export interface InterviewSessionResponse {
  id: number;
  candidateId: number;
  candidateName: string;
  targetJob: string;
  difficultyLevel: string | null;
  promptProfileId: number | null;
  createdAt: string;
  createdBy: number | null;
  deletedAt: string | null;
  deletedBy: number | null;
}

export interface InterviewSessionPayloadMeta {
  sessionId: number;
  candidateId: number;
  targetJob: string;
  difficultyLevel: string | null;
  promptProfileId: number | null;
  createdAt: string | null;
}

export interface InterviewSessionPayloadCandidate {
  candidateId: number;
  name: string;
  email: string | null;
  phone: string | null;
  birthDate: string | null;
  jobPosition: string | null;
  applyStatus: string | null;
}

export interface InterviewSessionPayloadPromptProfile {
  id: number;
  profileKey: string;
  targetJob: string | null;
  systemPrompt: string;
  outputSchema: unknown;
}

export interface InterviewSessionPayloadDocument {
  documentId: number;
  documentType: string;
  title: string;
  originalFileName: string;
  fileExt: string | null;
  mimeType: string | null;
  fileSize: number | null;
  extractStatus: string;
  extractedText: string | null;
  extractedSummary: string | null;
  structuredData: Record<string, unknown>;
}

export interface InterviewSessionPayloadPreview {
  session: InterviewSessionPayloadMeta;
  candidate: InterviewSessionPayloadCandidate;
  promptProfile: InterviewSessionPayloadPromptProfile | null;
  candidateDocuments: InterviewSessionPayloadDocument[];
}

export interface InterviewSessionCandidateOption {
  id: number;
  name: string;
  email: string;
}

export interface InterviewSessionPromptProfileOption {
  id: number;
  profileKey: string;
  targetJob: string | null;
}

export type InterviewSessionListResponse =
  PagedListResponse<InterviewSessionResponse>;

export interface InterviewQuestionGenerationTriggerRequest {
  triggerType?: string;
}

export interface InterviewSessionDetailResponse extends InterviewSessionResponse {
  assembledPayloadPreview: InterviewSessionPayloadPreview;
}
