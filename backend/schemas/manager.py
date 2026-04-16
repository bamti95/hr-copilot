from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

ManagerRoleType = Literal[
    "SUPER_ADMIN",
    "SYSTEM-MANAGER",
    "OPS_MANAGER",
    "RECRUIT_MANAGER",
    "DOC_REVIEWER",
    "QUALITY_MANAGER",
    "PROMPT_MANAGER",
]

ManagerStatus = Literal["ACTIVE", "INACTIVE", "LOCKED"]

class ManagerCreateRequest(BaseModel):
    login_id: str = Field(..., alias="loginId", min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    role_type: ManagerRoleType = Field(..., alias="roleType")
    status: ManagerStatus = "ACTIVE"

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)


class ManagerUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    role_type: ManagerRoleType = Field(..., alias="roleType")
    status: ManagerStatus = "ACTIVE"
    password: str | None = Field(None, min_length=8, max_length=100)

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)


class ManagerStatusUpdateRequest(BaseModel):
    status: ManagerStatus

    model_config = ConfigDict(str_strip_whitespace=True)

class ManagerResponse(BaseModel):
    id: int
    login_id: str = Field(..., alias="loginId")
    name: str
    email: str
    status: str
    role_type: str | None = Field(None, alias="roleType")
    last_login_at: datetime | None = Field(None, alias="lastLoginAt")
    created_at: datetime = Field(..., alias="createdAt")
    created_by: int | None = Field(None, alias="createdBy")
    deleted_at: datetime | None = Field(None, alias="deletedAt")
    deleted_by: int | None = Field(None, alias="deletedBy")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @staticmethod
    def from_entity(entity: object) -> "ManagerResponse":
        return ManagerResponse.model_validate(entity)    

class ManagerListResponse(BaseModel):
    items: list[ManagerResponse]
    total_count: int = Field(..., alias="totalCount")
    total_pages: int = Field(..., alias="totalPages")

    model_config = ConfigDict(populate_by_name=True)

    @staticmethod
    def of(items: list[ManagerResponse], total_count: int, total_pages: int) -> "ManagerListResponse":
        return ManagerListResponse(
            items=items,
            totalCount=total_count,
            totalPages=total_pages,
        )
