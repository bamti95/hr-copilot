"""공통 응답 스키마를 정의한다."""

from pydantic import BaseModel, ConfigDict

class BaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
