from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class AdminGroupRequest(BaseModel):
    group_name: str = Field(..., min_length=1, max_length=100)
    group_desc: Optional[str] = Field(None, max_length=500)
    use_tf: str = Field(default="Y", pattern="^(Y|N)$")

class AdminGroupResponse(BaseModel):
    id: int
    group_name: str
    group_desc: Optional[str]
    use_tf: str
    del_tf: str
    reg_adm: Optional[str]
    reg_date: datetime
    up_adm: Optional[str]
    up_date: Optional[datetime]
    del_adm: Optional[str]
    del_date: Optional[datetime]

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )
    
    @staticmethod
    def from_entity(entity) -> "AdminGroupResponse":
        return AdminGroupResponse.model_validate(entity)
    
    
class AdminGroupListResponse(BaseModel):
    items: list[AdminGroupResponse]
    total_count: int
    total_pages: int
    
    model_config = ConfigDict(populate_by_name=True)
    
    @staticmethod
    def of(items: list[AdminGroupResponse], total_count: int, total_pages: int) -> "AdminGroupListResponse":
        return AdminGroupListResponse(
            items=items,
            totalCount=total_count,
            totalPages=total_pages,
        )
    