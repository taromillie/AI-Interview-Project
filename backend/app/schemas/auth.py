"""认证与用户资料契约。"""
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6, max_length=64)
    email: EmailStr | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str | None = None
    role: str
    target_city: str | None = None
    years_of_exp: int | None = None
    target_position: str | None = None


class UserUpdateRequest(BaseModel):
    email: EmailStr | None = None
    target_city: str | None = Field(default=None, max_length=50)
    years_of_exp: int | None = Field(default=None, ge=0, le=60)
    target_position: str | None = Field(default=None, max_length=80)


class ProviderConfigRequest(BaseModel):
    provider_name: str = Field(min_length=1, max_length=30)
    api_key: str = Field(min_length=8, max_length=512)
    base_url: str | None = None
    model: str = Field(min_length=1, max_length=100)


class ProviderConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider_name: str
    base_url: str | None = None
    model: str
    is_active: bool
