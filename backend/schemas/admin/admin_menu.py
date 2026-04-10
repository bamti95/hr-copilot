from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

class AdminMenuRequest(BaseModel):
    parent_id: int | None = Field(None, alias="parentId")
    menu_name: str = Field(..., alias="menuName", min_length=1, max_length=100)
    menu_key: str = Field(..., alias="menuKey", min_length=1, max_length=100)
    menu_path: str | None = Field(None, alias="menuPath", max_length=255)
    depth: int = Field(1, ge=1)
    sort_no: int = Field(0, alias="sortNo", ge=0)
    icon: str | None = Field(None, max_length=100)
    use_tf: str | None = Field("Y", alias="useTf")
    del_tf: str | None = Field("N", alias="delTf")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )

class AdminMenuResponse(BaseModel):
    id: int
    parent_id: int | None = Field(None, alias="parentId")

    menu_name: str = Field(..., alias="menuName")
    menu_key: str = Field(..., alias="menuKey")
    menu_path: str | None = Field(None, alias="menuPath")
    depth: int
    sort_no: int = Field(..., alias="sortNo")
    icon: str | None = None

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
    def from_entity(entity) -> "AdminMenuResponse":
        return AdminMenuResponse.model_validate(entity)


class AdmMenuListResponse(BaseModel):
    items: list[AdminMenuResponse]
    total_count: int = Field(..., alias="totalCount")
    total_pages: int = Field(..., alias="totalPages")

    model_config = ConfigDict(populate_by_name=True)

    @staticmethod
    def of(
        items: list[AdminMenuResponse],
        total_count: int,
        total_pages: int,
    ) -> "AdmMenuListResponse":
        return AdmMenuListResponse(
            items=items,
            totalCount=total_count,
            totalPages=total_pages,
        )