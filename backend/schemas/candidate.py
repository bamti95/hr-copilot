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


class CandidateStatusPatchResponse(BaseModel):
    id: int
    apply_status: str
