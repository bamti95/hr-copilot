from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminRequest(BaseModel):
    group_id: int = Field(..., alias="groupId")
    login_id: str = Field(..., alias="loginId", min_length=3, max_length=100)
    password: str | None = Field(None, min_length=8, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr | None = None
    status: str | None = "ACTIVE"
    use_tf: str | None = Field("Y", alias="useTf")
    del_tf: str | None = Field("N", alias="delTf")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )


class AdminResponse(BaseModel):
    id: int
    group_id: int = Field(..., alias="groupId")
    login_id: str = Field(..., alias="loginId")
    name: str
    email: str | None
    status: str
    last_login_at: datetime | None = Field(None, alias="lastLoginAt")

    use_tf: str | None = Field(None, alias="useTf")
    del_tf: str | None = Field(None, alias="delTf")

    reg_adm: str | None = Field(None, alias="regAdm")
    reg_date: datetime = Field(..., alias="regDate")
    up_adm: str | None = Field(None, alias="upAdm")
    up_date: datetime | None = Field(None, alias="upDate")
    del_adm: str | None = Field(None, alias="delAdm")
    del_date: datetime | None = Field(None, alias="delDate")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    @staticmethod
    def from_entity(entity) -> "AdminResponse":
        return AdminResponse.model_validate(entity)


class AdminListResponse(BaseModel):
    items: list[AdminResponse]
    total_count: int = Field(..., alias="totalCount")
    total_pages: int = Field(..., alias="totalPages")

    model_config = ConfigDict(populate_by_name=True)

    @staticmethod
    def of(items: list[AdminResponse], total_count: int, total_pages: int) -> "AdminListResponse":
        return AdminListResponse(
            items=items,
            totalCount=total_count,
            totalPages=total_pages,
        )