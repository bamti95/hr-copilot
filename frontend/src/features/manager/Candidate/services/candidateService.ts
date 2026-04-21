import api from "../../../../services/api";
import type { PagingMeta } from "../../../../common/types/pagination";
import type {
  CandidateCreateRequest,
  CandidateDetailResponse,
  CandidateDocumentDetailResponse,
  CandidateDocumentResponse,
  CandidateDocumentReplaceRequest,
  CandidateDocumentUploadRequest,
  CandidateListRequest,
  CandidateListResponse,
  CandidateResponse,
  CandidateStatisticsResponse,
  CandidateStatusPatchRequest,
  CandidateUpdateRequest,
} from "../types";

interface CandidateApiResponse {
  id: number;
  name: string;
  email: string;
  phone: string;
  birth_date: string | null;
  apply_status: CandidateResponse["applyStatus"];
  created_at: string;
  created_by: number | null;
  updated_at: string;
  deleted_at: string | null;
  deleted_by: number | null;
}

interface CandidateDocumentApiResponse {
  id: number;
  document_type: CandidateDocumentResponse["documentType"];
  title: string;
  original_file_name: string;
  stored_file_name: string;
  file_path: string;
  file_ext: string | null;
  mime_type: string | null;
  file_size: number | null;
  extract_status: string;
  created_at: string;
}

interface CandidateDocumentDetailApiResponse extends CandidateDocumentApiResponse {
  extracted_text: string | null;
}

interface CandidateDetailApiResponse extends CandidateApiResponse {
  documents: CandidateDocumentApiResponse[];
}

interface CandidateListApiResponse {
  candidates: CandidateApiResponse[];
  pagination: {
    current_page: number;
    total_pages: number;
    total_items: number;
    items_per_page: number;
  };
}

interface CandidateStatisticsApiResponse {
  total_candidates: number;
  by_apply_status: { apply_status: string; count: number }[];
  by_target_job: { target_job: string; count: number }[];
  active_without_interview_session_count: number;
}

interface CandidateDocumentUploadApiResponse {
  candidate_id: number;
  count: number;
  documents: CandidateDocumentApiResponse[];
}

function mapCandidate(response: CandidateApiResponse): CandidateResponse {
  return {
    id: response.id,
    name: response.name,
    email: response.email,
    phone: response.phone,
    birthDate: response.birth_date,
    applyStatus: response.apply_status,
    createdAt: response.created_at,
    createdBy: response.created_by,
    updatedAt: response.updated_at,
    deletedAt: response.deleted_at,
    deletedBy: response.deleted_by,
  };
}

function mapDocument(response: CandidateDocumentApiResponse): CandidateDocumentResponse {
  return {
    id: response.id,
    documentType: response.document_type,
    title: response.title,
    originalFileName: response.original_file_name,
    storedFileName: response.stored_file_name,
    filePath: response.file_path,
    fileExt: response.file_ext,
    mimeType: response.mime_type,
    fileSize: response.file_size,
    extractStatus: response.extract_status,
    createdAt: response.created_at,
  };
}

function mapDocumentDetail(
  response: CandidateDocumentDetailApiResponse,
): CandidateDocumentDetailResponse {
  return {
    ...mapDocument(response),
    extractedText: response.extracted_text,
  };
}

function toPagingMeta(response: CandidateListApiResponse): PagingMeta {
  return {
    page: response.pagination.current_page,
    size: response.pagination.items_per_page,
    totalCount: response.pagination.total_items,
    totalPages: response.pagination.total_pages,
  };
}

function toCandidatePayload(requestBody: CandidateCreateRequest | CandidateUpdateRequest) {
  return {
    name: requestBody.name,
    email: requestBody.email,
    phone: requestBody.phone,
    birth_date: requestBody.birthDate || null,
  };
}

function mapCandidateStatistics(response: CandidateStatisticsApiResponse): CandidateStatisticsResponse {
  return {
    totalCandidates: response.total_candidates,
    byApplyStatus: response.by_apply_status.map((row) => ({
      applyStatus: row.apply_status,
      count: row.count,
    })),
    byTargetJob: response.by_target_job.map((row) => ({
      targetJob: row.target_job,
      count: row.count,
    })),
    activeWithoutInterviewSessionCount: response.active_without_interview_session_count,
  };
}

export async function fetchCandidateStatistics(): Promise<CandidateStatisticsResponse> {
  const response = await api.get<CandidateStatisticsApiResponse>("/candidates/statistics");
  return mapCandidateStatistics(response.data);
}

export async function fetchCandidateList(
  request: CandidateListRequest,
): Promise<CandidateListResponse> {
  const response = await api.get<CandidateListApiResponse>("/candidates", {
    params: {
      page: request.page,
      limit: request.limit,
      search: request.search || undefined,
      apply_status: request.applyStatus || undefined,
      target_job: request.targetJob?.trim() || undefined,
    },
  });

  return {
    items: response.data.candidates.map(mapCandidate),
    paging: toPagingMeta(response.data),
  };
}

export async function fetchCandidateDetail(
  candidateId: number,
): Promise<CandidateDetailResponse> {
  const response = await api.get<CandidateDetailApiResponse>(
    `/candidates/${candidateId}`,
  );

  return {
    ...mapCandidate(response.data),
    documents: response.data.documents.map(mapDocument),
  };
}

export async function createCandidate(
  requestBody: CandidateCreateRequest,
): Promise<CandidateResponse> {
  const response = await api.post<CandidateApiResponse>(
    "/candidates",
    toCandidatePayload(requestBody),
  );
  return mapCandidate(response.data);
}

export async function updateCandidate(
  candidateId: number,
  requestBody: CandidateUpdateRequest,
): Promise<CandidateResponse> {
  const response = await api.put<CandidateApiResponse>(
    `/candidates/${candidateId}`,
    toCandidatePayload(requestBody),
  );
  return mapCandidate(response.data);
}

export async function updateCandidateStatus(
  candidateId: number,
  requestBody: CandidateStatusPatchRequest,
) {
  await api.patch(`/candidates/${candidateId}/status`, {
    apply_status: requestBody.applyStatus,
  });
}

export async function deleteCandidate(candidateId: number) {
  await api.delete(`/candidates/${candidateId}`);
}

export async function uploadCandidateDocuments(
  candidateId: number,
  requestBody: CandidateDocumentUploadRequest,
): Promise<CandidateDocumentUploadResponse> {
  const formData = new FormData();

  requestBody.documentTypes.forEach((documentType) => {
    formData.append("document_types", documentType);
  });

  requestBody.files.forEach((file) => {
    formData.append("files", file);
  });

  const response = await api.post<CandidateDocumentUploadApiResponse>(
    `/candidates/${candidateId}/documents`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    },
  );

  return {
    candidateId: response.data.candidate_id,
    count: response.data.count,
    documents: response.data.documents.map(mapDocument),
  };
}

export async function downloadCandidateDocument(
  candidateId: number,
  documentId: number,
  fileName: string,
) {
  const response = await api.get<Blob>(
    `/candidates/${candidateId}/documents/${documentId}/download`,
    {
      responseType: "blob",
    },
  );

  const blobUrl = window.URL.createObjectURL(response.data);
  const anchor = document.createElement("a");
  anchor.href = blobUrl;
  anchor.download = fileName;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(blobUrl);
}

export async function fetchCandidateDocumentDetail(
  candidateId: number,
  documentId: number,
): Promise<CandidateDocumentDetailResponse> {
  const response = await api.get<CandidateDocumentDetailApiResponse>(
    `/candidates/${candidateId}/documents/${documentId}`,
  );

  return mapDocumentDetail(response.data);
}

export async function deleteCandidateDocument(
  candidateId: number,
  documentId: number,
) {
  await api.delete(`/candidates/${candidateId}/documents/${documentId}`);
}

export async function replaceCandidateDocument(
  candidateId: number,
  documentId: number,
  requestBody: CandidateDocumentReplaceRequest,
): Promise<CandidateDocumentResponse> {
  const formData = new FormData();
  formData.append("document_type", requestBody.documentType);
  formData.append("file", requestBody.file);

  const response = await api.put<CandidateDocumentApiResponse>(
    `/candidates/${candidateId}/documents/${documentId}`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    },
  );

  return mapDocument(response.data);
}
