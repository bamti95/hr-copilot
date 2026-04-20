from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PromptProfileCreateRequest(BaseModel):
    profile_key: str = Field(..., min_length=1, max_length=100)
    system_prompt: str = Field(..., min_length=1)
    output_schema: str | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class PromptProfileUpdateRequest(BaseModel):
    system_prompt: str = Field(..., min_length=1)
    output_schema: str | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class PromptProfileResponse(BaseModel):
    id: int
    profile_key: str
    system_prompt: str
    output_schema: str | None
    created_at: datetime
    created_by: int | None = None
    updated_at: datetime
    deleted_at: datetime | None = None
    deleted_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


class PromptProfilePagination(BaseModel):
    current_page: int
    total_pages: int
    total_items: int
    items_per_page: int


class PromptProfileListResponse(BaseModel):
    prompt_profiles: list[PromptProfileResponse]
    pagination: PromptProfilePagination


class PromptProfileDeleteResponse(BaseModel):
    id: int
    deleted_at: datetime
    deleted_by: int | None = None

    model_config = ConfigDict(from_attributes=True)
