import api from "../../../../services/api";
import type { PagingMeta } from "../../../../common/types/pagination";
import type {
  CandidateCreateRequest,
  CandidateDetailResponse,
  CandidateDocumentDetailResponse,
  CandidateDocumentResponse,
  CandidateDocumentReplaceRequest,
  CandidateDocumentUploadRequest,
  CandidateDocumentUploadResponse,
  CandidateBulkImportRequest,
  CandidateBulkImportResponse,
  CandidateListRequest,
  CandidateListResponse,
  CandidateResponse,
  CandidateSampleFolder,
  CandidateStatisticsResponse,
  CandidateStatusPatchRequest,
  CandidateUpdateRequest,
  DocumentBulkImportConfirmRequest,
  DocumentBulkImportConfirmResponse,
  DocumentBulkImportPreviewJobListResponse,
  DocumentBulkImportPreviewRequest,
  DocumentBulkImportPreviewJobResponse,
  DocumentBulkImportPreviewResponse,
  DocumentBulkImportPreviewStartResponse,
  ScreeningPreviewResult,
} from "../types";

interface CandidateRequestOptions {
  skipGlobalLoading?: boolean;
}

interface CandidateApiResponse {
  id: number;
  name: string;
  email: string;
  phone: string;
  birth_date: string | null;
  job_position: CandidateResponse["jobPosition"];
  apply_status: CandidateResponse["applyStatus"];
  created_at: string;
  created_by: number | null;
  created_name: string | null;
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
  screening_result: ScreeningPreviewApiResponse | null;
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

interface CandidateSampleFolderApiResponse {
  folder_name: string;
  candidate_count: number;
}

interface CandidateSampleFolderListApiResponse {
  folders: CandidateSampleFolderApiResponse[];
}

interface CandidateBulkImportErrorApiResponse {
  candidate_key: string;
  reason: string;
}

interface CandidateBulkImportApiResponse {
  folder_name: string;
  requested_count: number;
  created_count: number;
  skipped_count: number;
  document_count: number;
  errors: CandidateBulkImportErrorApiResponse[];
}

interface DocumentBulkImportConfirmApiResponse {
  job_id: number;
  requested_count: number;
  created_count: number;
  skipped_count: number;
  document_count: number;
  candidate_ids: number[];
  errors: {
    row_id: string | null;
    group_key: string | null;
    reason: string;
  }[];
}

interface CandidateProfileExtractionApiOutput {
  name: string | null;
  email: string | null;
  phone: string | null;
  birth_date: string | null;
  job_position: string | null;
  summary: string | null;
  confidence_score: number;
  missing_fields: string[];
  warnings: string[];
}

interface ScreeningPreviewApiResponse {
  recommendation: string;
  score: number;
  confidence: number;
  summary: string | null;
  fit_reasons: string[];
  risk_factors: string[];
  missing_evidence: string[];
  interview_focus: string[];
  suggested_next_action: string;
  score_breakdown: Record<string, unknown>;
  evidence_refs: Record<string, unknown>[];
  warnings: string[];
  decision_status: string | null;
}

interface DocumentBulkImportPreviewDocumentApiResponse {
  original_file_name: string;
  stored_file_name: string;
  file_path: string;
  file_ext: string | null;
  mime_type: string | null;
  file_size: number | null;
  document_type: string;
  extract_status: string;
  extract_strategy: string | null;
  extract_quality_score: number;
  extract_source_type: string | null;
  detected_document_type: string | null;
  extracted_text_length: number;
  extracted_text_preview: string | null;
  extract_meta: Record<string, unknown> | null;
  error_message: string | null;
}

interface DocumentBulkImportPreviewRowApiResponse {
  row_id: string;
  status: string;
  group_key: string;
  inferred_candidate_name: string | null;
  extracted_profile: CandidateProfileExtractionApiOutput;
  candidate: DocumentBulkImportPreviewResponse["rows"][number]["candidate"];
  documents: DocumentBulkImportPreviewDocumentApiResponse[];
  document_count: number;
  confidence_score: number;
  duplicate_candidate_id: number | null;
  errors: string[];
  warnings: string[];
  screening_preview: ScreeningPreviewApiResponse | null;
}

interface DocumentBulkImportPreviewApiResponse {
  job_id: number;
  upload_mode: DocumentBulkImportPreviewResponse["uploadMode"];
  summary: {
    total_groups: number;
    processed_groups: number;
    ready_count: number;
    needs_review_count: number;
    invalid_count: number;
    document_count: number;
  };
  rows: DocumentBulkImportPreviewRowApiResponse[];
}

interface DocumentBulkImportPreviewStartApiResponse {
  job_id: number;
  status: string;
  progress: number;
  current_step: string | null;
  message: string;
}

interface DocumentBulkImportPreviewJobApiResponse {
  job_id: number;
  status: string;
  progress: number;
  current_step: string | null;
  error_message: string | null;
  upload_mode: DocumentBulkImportPreviewResponse["uploadMode"] | null;
  summary: DocumentBulkImportPreviewApiResponse["summary"] | null;
  rows: DocumentBulkImportPreviewRowApiResponse[];
}

interface DocumentBulkImportPreviewJobListApiResponse {
  jobs: DocumentBulkImportPreviewJobApiResponse[];
}

function mapCandidate(response: CandidateApiResponse): CandidateResponse {
  return {
    id: response.id,
    name: response.name,
    email: response.email,
    phone: response.phone,
    birthDate: response.birth_date,
    jobPosition: response.job_position,
    applyStatus: response.apply_status,
    createdAt: response.created_at,
    createdBy: response.created_by,
    createdName: response.created_name,
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
    job_position: requestBody.jobPosition,
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

function mapCandidateSampleFolder(
  response: CandidateSampleFolderApiResponse,
): CandidateSampleFolder {
  return {
    folderName: response.folder_name,
    candidateCount: response.candidate_count,
  };
}

function mapScreeningPreview(
  response: ScreeningPreviewApiResponse | null | undefined,
): ScreeningPreviewResult | null {
  if (!response) {
    return null;
  }

  return {
    recommendation: response.recommendation,
    score: response.score,
    confidence: response.confidence,
    summary: response.summary,
    fitReasons: response.fit_reasons,
    riskFactors: response.risk_factors,
    missingEvidence: response.missing_evidence,
    interviewFocus: response.interview_focus,
    suggestedNextAction: response.suggested_next_action,
    scoreBreakdown: response.score_breakdown,
    evidenceRefs: response.evidence_refs,
    warnings: response.warnings,
    decisionStatus: response.decision_status,
  };
}

function mapDocumentBulkPreview(
  response: DocumentBulkImportPreviewApiResponse,
): DocumentBulkImportPreviewResponse {
  return {
    jobId: response.job_id,
    uploadMode: response.upload_mode,
    summary: {
      totalGroups: response.summary.total_groups,
      processedGroups: response.summary.processed_groups,
      readyCount: response.summary.ready_count,
      needsReviewCount: response.summary.needs_review_count,
      invalidCount: response.summary.invalid_count,
      documentCount: response.summary.document_count,
    },
    rows: response.rows.map((row) => ({
      rowId: row.row_id,
      status: row.status,
      groupKey: row.group_key,
      inferredCandidateName: row.inferred_candidate_name,
      extractedProfile: {
        name: row.extracted_profile.name,
        email: row.extracted_profile.email,
        phone: row.extracted_profile.phone,
        birthDate: row.extracted_profile.birth_date,
        jobPosition: row.extracted_profile.job_position,
        summary: row.extracted_profile.summary,
        confidenceScore: row.extracted_profile.confidence_score,
        missingFields: row.extracted_profile.missing_fields,
        warnings: row.extracted_profile.warnings,
      },
      candidate: row.candidate,
      documents: row.documents.map((document) => ({
        originalFileName: document.original_file_name,
        storedFileName: document.stored_file_name,
        filePath: document.file_path,
        fileExt: document.file_ext,
        mimeType: document.mime_type,
        fileSize: document.file_size,
        documentType: document.document_type as DocumentBulkImportPreviewResponse["rows"][number]["documents"][number]["documentType"],
        extractStatus: document.extract_status,
        extractStrategy: document.extract_strategy,
        extractQualityScore: document.extract_quality_score,
        extractSourceType: document.extract_source_type,
        detectedDocumentType: document.detected_document_type,
        extractedTextLength: document.extracted_text_length,
        extractedTextPreview: document.extracted_text_preview,
        extractMeta: document.extract_meta,
        errorMessage: document.error_message,
      })),
      documentCount: row.document_count,
      confidenceScore: row.confidence_score,
      duplicateCandidateId: row.duplicate_candidate_id,
      errors: row.errors,
      warnings: row.warnings,
      screeningPreview: mapScreeningPreview(row.screening_preview),
    })),
  };
}

function mapDocumentBulkPreviewStart(
  response: DocumentBulkImportPreviewStartApiResponse,
): DocumentBulkImportPreviewStartResponse {
  return {
    jobId: response.job_id,
    status: response.status,
    progress: response.progress,
    currentStep: response.current_step,
    message: response.message,
  };
}

function mapDocumentBulkPreviewJob(
  response: DocumentBulkImportPreviewJobApiResponse,
): DocumentBulkImportPreviewJobResponse {
  const preview =
    response.summary && response.upload_mode
      ? mapDocumentBulkPreview({
          job_id: response.job_id,
          upload_mode: response.upload_mode,
          summary: response.summary,
          rows: response.rows,
        })
      : null;

  return {
    jobId: response.job_id,
    status: response.status,
    progress: response.progress,
    currentStep: response.current_step,
    errorMessage: response.error_message,
    uploadMode: response.upload_mode,
    summary: preview?.summary ?? null,
    rows: preview?.rows ?? [],
  };
}

export async function fetchCandidateStatistics(
  options?: CandidateRequestOptions,
): Promise<CandidateStatisticsResponse> {
  const response = await api.get<CandidateStatisticsApiResponse>(
    "/candidates/statistics",
    {
      skipGlobalLoading: options?.skipGlobalLoading,
    },
  );
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
  options?: CandidateRequestOptions,
): Promise<CandidateDetailResponse> {
  const response = await api.get<CandidateDetailApiResponse>(
    `/candidates/${candidateId}`,
    {
      skipGlobalLoading: options?.skipGlobalLoading,
    },
  );

  return {
    ...mapCandidate(response.data),
    documents: response.data.documents.map(mapDocument),
    screeningResult: mapScreeningPreview(response.data.screening_result),
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

export async function fetchCandidateSampleFolders(): Promise<CandidateSampleFolder[]> {
  const response = await api.get<CandidateSampleFolderListApiResponse>(
    "/candidates/sample-folders",
  );
  return response.data.folders.map(mapCandidateSampleFolder);
}

export async function bulkImportCandidates(
  requestBody: CandidateBulkImportRequest,
): Promise<CandidateBulkImportResponse> {
  const response = await api.post<CandidateBulkImportApiResponse>(
    "/candidates/bulk-import",
    {
      folder_name: requestBody.folderName,
    },
  );

  return {
    folderName: response.data.folder_name,
    requestedCount: response.data.requested_count,
    createdCount: response.data.created_count,
    skippedCount: response.data.skipped_count,
    documentCount: response.data.document_count,
    errors: response.data.errors.map((error) => ({
      candidateKey: error.candidate_key,
      reason: error.reason,
    })),
  };
}

export async function previewDocumentBulkImport(
  requestBody: DocumentBulkImportPreviewRequest,
): Promise<DocumentBulkImportPreviewStartResponse> {
  const formData = new FormData();
  if (requestBody.defaultJobPosition?.trim()) {
    formData.append("default_job_position", requestBody.defaultJobPosition.trim());
  }
  formData.append("default_apply_status", requestBody.defaultApplyStatus || "APPLIED");

  if (requestBody.mode === "ZIP") {
    if (!requestBody.zipFile) {
      throw new Error("ZIP 파일을 선택해주세요.");
    }
    formData.append("zip_file", requestBody.zipFile);
    const response = await api.post<DocumentBulkImportPreviewStartApiResponse>(
      "/candidates/document-bulk/preview",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      },
    );
    return mapDocumentBulkPreviewStart(response.data);
  }

  if (!requestBody.files || requestBody.files.length === 0) {
    throw new Error("문서 파일을 1개 이상 선택해주세요.");
  }
  requestBody.files.forEach((file) => {
    formData.append("files", file);
  });
  const response = await api.post<DocumentBulkImportPreviewStartApiResponse>(
    "/candidates/document-bulk/preview/files",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    },
  );
  return mapDocumentBulkPreviewStart(response.data);
}

export async function fetchDocumentBulkPreviewJob(
  jobId: number,
): Promise<DocumentBulkImportPreviewJobResponse> {
  const response = await api.get<DocumentBulkImportPreviewJobApiResponse>(
    `/candidates/document-bulk/preview/jobs/${jobId}`,
    {
      skipGlobalLoading: true,
    },
  );
  return mapDocumentBulkPreviewJob(response.data);
}

export async function fetchDocumentBulkPreviewJobs(
  request: { activeOnly?: boolean; limit?: number } = {},
): Promise<DocumentBulkImportPreviewJobListResponse> {
  const response = await api.get<DocumentBulkImportPreviewJobListApiResponse>(
    "/candidates/document-bulk/preview/jobs",
    {
      params: {
        active_only: request.activeOnly ?? true,
        limit: request.limit ?? 10,
      },
      skipGlobalLoading: true,
    },
  );
  return {
    jobs: response.data.jobs.map(mapDocumentBulkPreviewJob),
  };
}

export async function confirmDocumentBulkImport(
  requestBody: DocumentBulkImportConfirmRequest,
): Promise<DocumentBulkImportConfirmResponse> {
  const response = await api.post<DocumentBulkImportConfirmApiResponse>(
    "/candidates/document-bulk/import",
    {
      job_id: requestBody.jobId,
      selected_row_ids: requestBody.selectedRowIds,
    },
  );
  return {
    jobId: response.data.job_id,
    requestedCount: response.data.requested_count,
    createdCount: response.data.created_count,
    skippedCount: response.data.skipped_count,
    documentCount: response.data.document_count,
    candidateIds: response.data.candidate_ids,
    errors: response.data.errors.map((error) => ({
      rowId: error.row_id,
      groupKey: error.group_key,
      reason: error.reason,
    })),
  };
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
  options?: CandidateRequestOptions,
): Promise<CandidateDocumentDetailResponse> {
  const response = await api.get<CandidateDocumentDetailApiResponse>(
    `/candidates/${candidateId}/documents/${documentId}`,
    {
      skipGlobalLoading: options?.skipGlobalLoading,
    },
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
