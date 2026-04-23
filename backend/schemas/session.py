from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from schemas.session_generation import CandidateInterviewPrepInput


class SessionSchemaBase(BaseModel):
    # Pydantic v2 equivalent of orm_mode=True
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class SessionCreateRequest(BaseModel):
    candidate_id: int = Field(..., gt=0)
    target_job: str = Field(..., min_length=1, max_length=50)
    difficulty_level: str | None = Field(default=None, max_length=20)
    prompt_profile_id: int = Field(..., gt=0)

    model_config = ConfigDict(str_strip_whitespace=True)


class SessionUpdateRequest(BaseModel):
    target_job: str = Field(..., min_length=1, max_length=50)
    difficulty_level: str | None = Field(default=None, max_length=20)

    model_config = ConfigDict(str_strip_whitespace=True)


class SessionResponse(SessionSchemaBase):
    id: int
    candidate_id: int
    candidate_name: str
    target_job: str
    difficulty_level: str | None = None
    prompt_profile_id: int | None = None
    created_at: datetime
    created_by: int | None = None
    deleted_at: datetime | None = None
    deleted_by: int | None = None


class SessionDeleteResponse(SessionSchemaBase):
    id: int
    deleted_at: datetime
    deleted_by: int | None = None


class SessionPagination(BaseModel):
    current_page: int
    total_pages: int
    total_items: int
    items_per_page: int


class SessionListData(BaseModel):
    interview_sessions: list[SessionResponse]
    pagination: SessionPagination


class SessionSingleResponse(BaseModel):
    success: bool = True
    data: SessionResponse
    message: str


class SessionDetailResponse(SessionResponse):
    assembled_payload_preview: CandidateInterviewPrepInput


class SessionDetailSingleResponse(BaseModel):
    success: bool = True
    data: SessionDetailResponse
    message: str


class SessionListResponse(BaseModel):
    success: bool = True
    data: SessionListData
    message: str


class SessionDeleteResultResponse(BaseModel):
    success: bool = True
    data: SessionDeleteResponse
    message: str


class SessionGenerateQuestionsRequest(BaseModel):
    trigger_type: str = Field(default="MANUAL", min_length=1, max_length=50)

    model_config = ConfigDict(str_strip_whitespace=True)


class SessionTriggerData(BaseModel):
    session_id: int
    trigger_type: str


class SessionTriggerResponse(BaseModel):
    success: bool = True
    data: SessionTriggerData
    message: str
