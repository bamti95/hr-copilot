from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from schemas.admin.admin import AdminResponse

class LoginRequest(BaseModel):
    login_id: str = Field(..., alias="loginId")
    password: str

    model_config = ConfigDict(populate_by_name=True)

class MenuPermissionResponse(BaseModel):
    menu_id: int = Field(..., alias="menuId")
    menu_key: str = Field(..., alias="menuKey")
    menu_name: str = Field(..., alias="menuName")
    menu_path: str | None = Field(None, alias="menuPath")
    read_tf: str = Field(..., alias="readTf")
    write_tf: str = Field(..., alias="writeTf")
    delete_tf: str = Field(..., alias="deleteTf")

    model_config = ConfigDict(populate_by_name=True)


class TokenPairResponse(BaseModel):
    access_token: str = Field(..., alias="accessToken")
    refresh_token: str = Field(..., alias="refreshToken")
    token_type: str = Field(..., alias="tokenType")
    admin: AdminResponse
    permissions: list[MenuPermissionResponse]

    model_config = ConfigDict(populate_by_name=True)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., alias="refreshToken")

    model_config = ConfigDict(populate_by_name=True)


class RefreshTokenResponse(BaseModel):
    access_token: str = Field(..., alias="accessToken")
    refresh_token: str = Field(..., alias="refreshToken")
    token_type: str = Field(..., alias="tokenType")

    model_config = ConfigDict(populate_by_name=True)


class MeResponse(BaseModel):
    admin: AdminResponse
    permissions: list[MenuPermissionResponse]

    model_config = ConfigDict(populate_by_name=True)


class LogoutRequest(BaseModel):
    refresh_token: str | None = Field(None, alias="refreshToken")

    model_config = ConfigDict(populate_by_name=True)