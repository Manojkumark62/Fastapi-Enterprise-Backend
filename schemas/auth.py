"""Request/response schemas for the auth flow."""

from pydantic import BaseModel, EmailStr, Field, field_validator

from utils.password_policy import validate_password_strength


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)

    @field_validator("password")
    @classmethod
    def _check_password_strength(cls, v: str) -> str:
        # Raises ValueError with a specific message if the password is weak;
        # Pydantic surfaces that as a 422 automatically.
        validate_password_strength(v)
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _check_password_strength(cls, v: str) -> str:
        validate_password_strength(v)
        return v


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _check_reset_password_strength(cls, v: str) -> str:
        validate_password_strength(v)
        return v
