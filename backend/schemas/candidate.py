from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CandidateCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=1, max_length=50)
    birth_date: date | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class CandidateUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=1, max_length=50)
    birth_date: date | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class CandidateStatusPatchRequest(BaseModel):
    """apply_status는 서비스에서 ApplyStatus로 검증합니다 (잘못된 값은 HTTP 400)."""

    apply_status: str = Field(..., min_length=1, max_length=30)

    model_config = ConfigDict(str_strip_whitespace=True)


class CandidateResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    birth_date: date | None = None
    apply_status: str
    created_at: datetime
    created_by: int | None = None
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
