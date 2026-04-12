from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from schemas.admin.admin_group_menu import (
    AdminGroupMenuPermissionRequest,
    AdminGroupMenuPermissionResponse,
)


class AdminGroupRequest(BaseModel):
    group_name: str = Field(..., alias="groupName", min_length=1, max_length=100)
    group_desc: Optional[str] = Field(None, alias="groupDesc", max_length=500)
    use_tf: str = Field(default="Y", alias="useTf", pattern="^(Y|N)$")
    menu_permissions: list[AdminGroupMenuPermissionRequest] = Field(
        default_factory=list,
        alias="menuPermissions",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )

class AdminGroupResponse(BaseModel):
    id: int
    group_name: str = Field(..., alias="groupName")
    group_desc: Optional[str] = Field(None, alias="groupDesc")
    use_tf: str = Field(..., alias="useTf")
    del_tf: str = Field(..., alias="delTf")
    reg_adm: Optional[str] = Field(None, alias="regAdm")
    reg_date: datetime = Field(..., alias="regDate")
    up_adm: Optional[str] = Field(None, alias="upAdm")
    up_date: Optional[datetime] = Field(None, alias="upDate")
    del_adm: Optional[str] = Field(None, alias="delAdm")
    del_date: Optional[datetime] = Field(None, alias="delDate")
    menu_permissions: list[AdminGroupMenuPermissionResponse] = Field(
        default_factory=list,
        alias="menuPermissions",
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    @staticmethod
    def from_entity(
        entity,
        menu_permissions: list[AdminGroupMenuPermissionResponse] | None = None,
    ) -> "AdminGroupResponse":
        payload = AdminGroupResponse.model_validate(entity).model_dump(by_alias=True)
        payload["menuPermissions"] = menu_permissions or []
        return AdminGroupResponse(**payload)


class AdminGroupListResponse(BaseModel):
    items: list[AdminGroupResponse]
    total_count: int = Field(..., alias="totalCount")
    total_pages: int = Field(..., alias="totalPages")

    model_config = ConfigDict(populate_by_name=True)

    @staticmethod
    def of(
        items: list[AdminGroupResponse],
        total_count: int,
        total_pages: int,
    ) -> "AdminGroupListResponse":
        return AdminGroupListResponse(
            items=items,
            totalCount=total_count,
            totalPages=total_pages,
        )
