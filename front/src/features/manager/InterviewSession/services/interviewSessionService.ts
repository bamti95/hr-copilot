import api from "../../../../services/api";
import { fetchCandidateList } from "../../Candidate/services/candidateService";
import type { CandidateResponse } from "../../Candidate/types";
import type {
  InterviewSessionCandidateOption,
  InterviewSessionCreateRequest,
  InterviewSessionListRequest,
  InterviewSessionListResponse,
  InterviewSessionResponse,
  InterviewSessionUpdateRequest,
} from "../types";

interface SessionApiResponse {
  id: number;
  candidate_id: number;
  candidate_name: string;
  target_job: string;
  difficulty_level: string | null;
  created_at: string;
  created_by: number | null;
  deleted_at: string | null;
  deleted_by: number | null;
}

interface SessionListApiResponse {
  interview_sessions: SessionApiResponse[];
  pagination: {
    current_page: number;
    total_pages: number;
    total_items: number;
    items_per_page: number;
  };
}

interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  message: string;
}

function mapSession(response: SessionApiResponse): InterviewSessionResponse {
  return {
    id: response.id,
    candidateId: response.candidate_id,
    candidateName: response.candidate_name,
    targetJob: response.target_job,
    difficultyLevel: response.difficulty_level,
    createdAt: response.created_at,
    createdBy: response.created_by,
    deletedAt: response.deleted_at,
    deletedBy: response.deleted_by,
  };
}

function mapCandidateOption(
  response: CandidateResponse,
): InterviewSessionCandidateOption {
  return {
    id: response.id,
    name: response.name,
    email: response.email,
  };
}

export async function fetchInterviewSessionList(
  request: InterviewSessionListRequest,
): Promise<InterviewSessionListResponse> {
  const response = await api.get<ApiEnvelope<SessionListApiResponse>>(
    "/interview-sessions",
    {
      params: {
        page: request.page,
        limit: request.limit,
        candidate_id: request.candidateId,
        target_job: request.targetJob || undefined,
      },
    },
  );

  return {
    items: response.data.data.interview_sessions.map(mapSession),
    paging: {
      page: response.data.data.pagination.current_page,
      size: response.data.data.pagination.items_per_page,
      totalCount: response.data.data.pagination.total_items,
      totalPages: response.data.data.pagination.total_pages,
    },
  };
}

export async function fetchInterviewSessionDetail(
  sessionId: number,
): Promise<InterviewSessionResponse> {
  const response = await api.get<ApiEnvelope<SessionApiResponse>>(
    `/interview-sessions/${sessionId}`,
  );
  return mapSession(response.data.data);
}

export async function createInterviewSession(
  requestBody: InterviewSessionCreateRequest,
): Promise<InterviewSessionResponse> {
  const response = await api.post<ApiEnvelope<SessionApiResponse>>(
    "/interview-sessions",
    {
      candidate_id: requestBody.candidateId,
      target_job: requestBody.targetJob,
      difficulty_level: requestBody.difficultyLevel ?? null,
    },
  );
  return mapSession(response.data.data);
}

export async function updateInterviewSession(
  sessionId: number,
  requestBody: InterviewSessionUpdateRequest,
): Promise<InterviewSessionResponse> {
  const response = await api.put<ApiEnvelope<SessionApiResponse>>(
    `/interview-sessions/${sessionId}`,
    {
      target_job: requestBody.targetJob,
      difficulty_level: requestBody.difficultyLevel ?? null,
    },
  );
  return mapSession(response.data.data);
}

export async function deleteInterviewSession(sessionId: number): Promise<void> {
  await api.delete(`/interview-sessions/${sessionId}`);
}

export async function fetchInterviewSessionCandidateOptions(): Promise<
  InterviewSessionCandidateOption[]
> {
  const response = await fetchCandidateList({
    page: 1,
    limit: 100,
  });

  return response.items.map(mapCandidateOption);
}
