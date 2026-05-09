from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

class CandidateCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=1, max_length=50)
    job_position: str | None = Field(default=None, max_length=100)
    birth_date: date | None = None
    model_config = ConfigDict(str_strip_whitespace=True)

class CandidateUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=1, max_length=50)
    job_position: str | None = Field(default=None, max_length=100)
    birth_date: date | None = None
    model_config = ConfigDict(str_strip_whitespace=True)


class CandidateStatusPatchRequest(BaseModel):
    """apply_status는 서비스에서 ApplyStatus로 검증 (잘못된 값은 HTTP 400)."""

    apply_status: str = Field(..., min_length=1, max_length=30)
    model_config = ConfigDict(str_strip_whitespace=True)


class CandidateResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    birth_date: date | None = None
    job_position: str | None
    apply_status: str
    created_at: datetime
    created_by: int | None = None
    created_name: str | None = None
    updated_at: datetime
    deleted_at: datetime | None = None
    deleted_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


class CandidateDocumentResponse(BaseModel):
    id: int
    document_type: str
    title: str
    original_file_name: str
    stored_file_name: str
    file_path: str
    file_ext: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    extract_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateDocumentDetailResponse(CandidateDocumentResponse):
    extracted_text: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CandidateDetailResponse(CandidateResponse):
    documents: list[CandidateDocumentResponse] = Field(default_factory=list)


class CandidateDeleteResponse(BaseModel):
    id: int
    deleted_at: datetime
    deleted_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


class CandidatePagination(BaseModel):
    current_page: int
    total_pages: int
    total_items: int
    items_per_page: int


class CandidateListResponse(BaseModel):
    candidates: list[CandidateResponse]
    pagination: CandidatePagination


class CandidateDocumentUploadResponse(BaseModel):
    candidate_id: int
    count: int
    documents: list[CandidateDocumentResponse]


class CandidateSampleFolderResponse(BaseModel):
    folder_name: str
    candidate_count: int


class CandidateSampleFolderListResponse(BaseModel):
    folders: list[CandidateSampleFolderResponse]


class CandidateBulkImportRequest(BaseModel):
    folder_name: str = Field(..., min_length=1, max_length=255)
    model_config = ConfigDict(str_strip_whitespace=True)


class CandidateBulkImportError(BaseModel):
    candidate_key: str
    reason: str


class CandidateBulkImportResponse(BaseModel):
    folder_name: str
    requested_count: int
    created_count: int
    skipped_count: int
    document_count: int
    errors: list[CandidateBulkImportError] = Field(default_factory=list)


class CandidateProfileExtractionOutput(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    birth_date: str | None = Field(default=None, max_length=20)
    job_position: str | None = Field(default=None, max_length=100)
    summary: str | None = Field(default=None, max_length=1000)
    confidence_score: float = Field(default=0, ge=0, le=1)
    missing_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DocumentBulkImportPreviewDocument(BaseModel):
    original_file_name: str
    stored_file_name: str
    file_path: str
    file_ext: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    document_type: str
    extract_status: str
    extract_strategy: str | None = None
    extract_quality_score: float = 0
    extract_source_type: str | None = None
    detected_document_type: str | None = None
    extracted_text_length: int = 0
    extracted_text_preview: str | None = None
    extract_meta: dict | None = None
    error_message: str | None = None


class DocumentBulkImportPreviewRow(BaseModel):
    row_id: str
    status: str
    group_key: str
    inferred_candidate_name: str | None = None
    extracted_profile: CandidateProfileExtractionOutput
    candidate: dict
    documents: list[DocumentBulkImportPreviewDocument]
    document_count: int
    confidence_score: float
    duplicate_candidate_id: int | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DocumentBulkImportPreviewSummary(BaseModel):
    total_groups: int
    processed_groups: int = 0
    ready_count: int
    needs_review_count: int
    invalid_count: int
    document_count: int


class DocumentBulkImportPreviewResponse(BaseModel):
    job_id: int
    upload_mode: str
    summary: DocumentBulkImportPreviewSummary
    rows: list[DocumentBulkImportPreviewRow]


class DocumentBulkImportPreviewStartResponse(BaseModel):
    job_id: int
    status: str
    progress: int
    current_step: str | None = None
    message: str


class DocumentBulkImportPreviewJobResponse(BaseModel):
    job_id: int
    status: str
    progress: int
    current_step: str | None = None
    error_message: str | None = None
    upload_mode: str | None = None
    summary: DocumentBulkImportPreviewSummary | None = None
    rows: list[DocumentBulkImportPreviewRow] = Field(default_factory=list)


class DocumentBulkImportPreviewJobListResponse(BaseModel):
    jobs: list[DocumentBulkImportPreviewJobResponse] = Field(default_factory=list)


class DocumentBulkImportConfirmRequest(BaseModel):
    job_id: int = Field(..., ge=1)
    selected_row_ids: list[str] = Field(default_factory=list)


class DocumentBulkImportConfirmError(BaseModel):
    row_id: str | None = None
    group_key: str | None = None
    reason: str


class DocumentBulkImportConfirmResponse(BaseModel):
    job_id: int
    requested_count: int
    created_count: int
    skipped_count: int
    document_count: int
    candidate_ids: list[int] = Field(default_factory=list)
    errors: list[DocumentBulkImportConfirmError] = Field(default_factory=list)


class CandidateDocumentDeleteResponse(BaseModel):
    id: int
    deleted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateStatusPatchResponse(BaseModel):
    id: int
    apply_status: str


class ApplyStatusCountRow(BaseModel):
    apply_status: str
    count: int


class TargetJobCountRow(BaseModel):
    target_job: str
    count: int


class CandidateStatisticsResponse(BaseModel):
    total_candidates: int
    by_apply_status: list[ApplyStatusCountRow]
    by_target_job: list[TargetJobCountRow]
    active_without_interview_session_count: int
