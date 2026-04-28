import api from "../../../../services/api";
import { fetchCandidateList } from "../../Candidate/services/candidateService";
import type { CandidateResponse } from "../../Candidate/types";
import type {
  InterviewSessionCandidateOption,
  InterviewSessionCreateRequest,
  InterviewSessionDetailResponse,
  InterviewQuestionGenerationStatus,
  InterviewQuestionReviewStatus,
  InterviewQuestionGenerationStatusResponse,
  InterviewQuestionGenerationTriggerRequest,
  InterviewSessionListRequest,
  InterviewSessionListResponse,
  InterviewSessionPayloadPreview,
  InterviewSessionResponse,
  InterviewSessionUpdateRequest,
} from "../types";

interface SessionApiResponse {
  id: number;
  candidate_id: number;
  candidate_name: string;
  target_job: string;
  difficulty_level: string | null;
  prompt_profile_id: number | null;
  created_at: string;
  created_by: number | null;
  deleted_at: string | null;
  deleted_by: number | null;
  question_generation_status: InterviewQuestionGenerationStatus;
  question_generation_error: string | null;
  question_generation_requested_at: string | null;
  question_generation_completed_at: string | null;
}

interface GeneratedQuestionApiResponse {
  id: string;
  category: string;
  question_text: string;
  generation_basis: string;
  document_evidence: string[];
  evaluation_guide: string;
  predicted_answer: string;
  predicted_answer_basis: string;
  follow_up_question: string;
  follow_up_basis: string;
  risk_tags: string[];
  competency_tags: string[];
  review: {
    question_id: string;
    status: InterviewQuestionReviewStatus;
    reason: string;
    reject_reason: string;
    recommended_revision: string;
  };
  score: number;
  score_reason: string;
}

interface QuestionGenerationStatusApiResponse {
  session_id: number;
  status: InterviewQuestionGenerationStatus;
  error: string | null;
  requested_at: string | null;
  completed_at: string | null;
  progress?: Array<{
    key: string;
    label: string;
    status: string;
    started_at?: string | null;
    completed_at?: string | null;
    attempt?: number | null;
    error?: string | null;
  }>;
  generation_source: Record<string, string>;
  questions: GeneratedQuestionApiResponse[];
}

interface SessionPayloadMetaApiResponse {
  session_id: number;
  candidate_id: number;
  target_job: string;
  difficulty_level: string | null;
  prompt_profile_id: number | null;
  created_at: string | null;
}

interface SessionPayloadCandidateApiResponse {
  candidate_id: number;
  name: string;
  email: string | null;
  phone: string | null;
  birth_date: string | null;
  job_position: string | null;
  apply_status: string | null;
}

interface SessionPayloadPromptProfileApiResponse {
  id: number;
  profile_key: string;
  target_job: string | null;
  system_prompt: string;
  output_schema: unknown;
}

interface SessionPayloadDocumentApiResponse {
  document_id: number;
  document_type: string;
  title: string;
  original_file_name: string;
  file_ext: string | null;
  mime_type: string | null;
  file_size: number | null;
  extract_status: string;
  extracted_text: string | null;
  extracted_summary: string | null;
  structured_data: Record<string, unknown>;
}

interface SessionDetailApiResponse extends SessionApiResponse {
  assembled_payload_preview: {
    session: SessionPayloadMetaApiResponse;
    candidate: SessionPayloadCandidateApiResponse;
    prompt_profile: SessionPayloadPromptProfileApiResponse | null;
    candidate_documents: SessionPayloadDocumentApiResponse[];
  };
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
    promptProfileId: response.prompt_profile_id,
    createdAt: response.created_at,
    createdBy: response.created_by,
    deletedAt: response.deleted_at,
    deletedBy: response.deleted_by,
    questionGenerationStatus: response.question_generation_status,
    questionGenerationError: response.question_generation_error,
    questionGenerationRequestedAt: response.question_generation_requested_at,
    questionGenerationCompletedAt: response.question_generation_completed_at,
  };
}

function mapPayloadPreview(
  response: SessionDetailApiResponse["assembled_payload_preview"],
): InterviewSessionPayloadPreview {
  return {
    session: {
      sessionId: response.session.session_id,
      candidateId: response.session.candidate_id,
      targetJob: response.session.target_job,
      difficultyLevel: response.session.difficulty_level,
      promptProfileId: response.session.prompt_profile_id,
      createdAt: response.session.created_at,
    },
    candidate: {
      candidateId: response.candidate.candidate_id,
      name: response.candidate.name,
      email: response.candidate.email,
      phone: response.candidate.phone,
      birthDate: response.candidate.birth_date,
      jobPosition: response.candidate.job_position,
      applyStatus: response.candidate.apply_status,
    },
    promptProfile: response.prompt_profile
      ? {
          id: response.prompt_profile.id,
          profileKey: response.prompt_profile.profile_key,
          targetJob: response.prompt_profile.target_job,
          systemPrompt: response.prompt_profile.system_prompt,
          outputSchema: response.prompt_profile.output_schema,
        }
      : null,
    candidateDocuments: response.candidate_documents.map((document) => ({
      documentId: document.document_id,
      documentType: document.document_type,
      title: document.title,
      originalFileName: document.original_file_name,
      fileExt: document.file_ext,
      mimeType: document.mime_type,
      fileSize: document.file_size,
      extractStatus: document.extract_status,
      extractedText: document.extracted_text,
      extractedSummary: document.extracted_summary,
      structuredData: document.structured_data,
    })),
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
        target_job: request.targetJob || undefined,
      },
    },
  );

  const allItems = response.data.data.interview_sessions.map(mapSession);
  const normalizedCandidateName = request.candidateName?.trim().toLowerCase();
  const filteredItems = normalizedCandidateName
    ? allItems.filter((item) =>
        item.candidateName.toLowerCase().includes(normalizedCandidateName),
      )
    : allItems;

  return {
    items: filteredItems,
    paging: {
      page: response.data.data.pagination.current_page,
      size: response.data.data.pagination.items_per_page,
      totalCount: normalizedCandidateName
        ? filteredItems.length
        : response.data.data.pagination.total_items,
      totalPages: normalizedCandidateName
        ? Math.ceil(filteredItems.length / response.data.data.pagination.items_per_page)
        : response.data.data.pagination.total_pages,
    },
  };
}

export async function fetchInterviewSessionDetail(
  sessionId: number,
): Promise<InterviewSessionDetailResponse> {
  const response = await api.get<ApiEnvelope<SessionDetailApiResponse>>(
    `/interview-sessions/${sessionId}`,
  );
  return {
    ...mapSession(response.data.data),
    assembledPayloadPreview: mapPayloadPreview(
      response.data.data.assembled_payload_preview,
    ),
  };
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
      prompt_profile_id: requestBody.promptProfileId ?? null,
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

export async function triggerInterviewQuestionGeneration(
  sessionId: number,
  requestBody?: InterviewQuestionGenerationTriggerRequest,
): Promise<void> {
  await api.post(`/interview-sessions/${sessionId}/generate-questions`, {
    trigger_type: requestBody?.triggerType?.trim() || "MANUAL",
  }, {
    skipGlobalLoading: true,
  });
}

export async function fetchInterviewQuestionGenerationStatus(
  sessionId: number,
): Promise<InterviewQuestionGenerationStatusResponse> {
  const response = await api.get<ApiEnvelope<QuestionGenerationStatusApiResponse>>(
    `/interview-sessions/${sessionId}/question-generation`,
    {
      skipGlobalLoading: true,
    },
  );
  const data = response.data.data;

  return {
    sessionId: data.session_id,
    status: data.status,
    error: data.error,
    requestedAt: data.requested_at,
    completedAt: data.completed_at,
    progress: (data.progress ?? []).map((step) => ({
      key: step.key,
      label: step.label,
      status:
        step.status === "PROCESSING" ||
        step.status === "COMPLETED" ||
        step.status === "FAILED"
          ? step.status
          : "PENDING",
      startedAt: step.started_at ?? null,
      completedAt: step.completed_at ?? null,
      attempt: step.attempt ?? 0,
      error: step.error ?? null,
    })),
    generationSource: data.generation_source ?? {},
    questions: data.questions.map((question) => ({
      id: question.id,
      category: question.category,
      questionText: question.question_text,
      generationBasis: question.generation_basis,
      documentEvidence: question.document_evidence,
      evaluationGuide: question.evaluation_guide,
      predictedAnswer: question.predicted_answer,
      predictedAnswerBasis: question.predicted_answer_basis,
      followUpQuestion: question.follow_up_question,
      followUpBasis: question.follow_up_basis,
      riskTags: question.risk_tags,
      competencyTags: question.competency_tags,
      review: {
        questionId: question.review.question_id,
        status: question.review.status,
        reason: question.review.reason,
        rejectReason: question.review.reject_reason,
        recommendedRevision: question.review.recommended_revision,
      },
      score: question.score,
      scoreReason: question.score_reason,
    })),
  };
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
