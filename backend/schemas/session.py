"""면접 세션과 질문 생성 상태 API 스키마를 정의한다."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from schemas.session_generation import CandidateInterviewPrepInput
from ai.interview_graph.schemas import InterviewQuestionItem


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
    created_name: str | None = None
    deleted_at: datetime | None = None
    deleted_by: int | None = None
    question_generation_status: str = "NOT_REQUESTED"
    question_generation_error: str | None = None
    question_generation_requested_at: datetime | None = None
    question_generation_completed_at: datetime | None = None
    question_generation_progress: list[dict] | None = None


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
    target_question_ids: list[str] = Field(default_factory=list)
    graph_impl: str = Field(default="default", max_length=20)

    model_config = ConfigDict(str_strip_whitespace=True)


class SessionTriggerData(BaseModel):
    session_id: int
    trigger_type: str
    question_generation_status: str = "QUEUED"


class SessionTriggerResponse(BaseModel):
    success: bool = True
    data: SessionTriggerData
    message: str


class SessionQuestionGenerationData(BaseModel):
    session_id: int
    status: str
    error: str | None = None
    requested_at: datetime | None = None
    completed_at: datetime | None = None
    progress: list[dict] = Field(default_factory=list)
    generation_source: dict[str, str] = Field(default_factory=dict)
    questions: list[InterviewQuestionItem] = Field(default_factory=list)


class SessionQuestionGenerationResponse(BaseModel):
    success: bool = True
    data: SessionQuestionGenerationData
    message: str

