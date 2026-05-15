"""인증 API 요청과 응답 스키마를 정의한다."""

from pydantic import BaseModel, ConfigDict, Field

from schemas.manager import ManagerResponse


class LoginRequest(BaseModel):
    login_id: str = Field(..., alias="loginId")
    password: str

    model_config = ConfigDict(populate_by_name=True)


class LoginResponse(BaseModel):
    access_token: str = Field(..., alias="accessToken")
    refresh_token: str = Field(..., alias="refreshToken")
    token_type: str = Field(..., alias="tokenType")
    manager: ManagerResponse

    model_config = ConfigDict(populate_by_name=True)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., alias="refreshToken")

    model_config = ConfigDict(populate_by_name=True)


class RefreshTokenResponse(BaseModel):
    access_token: str = Field(..., alias="accessToken")
    refresh_token: str = Field(..., alias="refreshToken")
    token_type: str = Field(..., alias="tokenType")

    model_config = ConfigDict(populate_by_name=True)


class LogoutRequest(BaseModel):
    refresh_token: str | None = Field(None, alias="refreshToken")

    model_config = ConfigDict(populate_by_name=True)

