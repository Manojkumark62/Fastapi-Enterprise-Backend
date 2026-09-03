"""User schemas — response and update shapes. Registration lives in schemas/auth.py."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    is_verified: bool
    is_superuser: bool
    last_login_at: datetime | None
    created_at: datetime


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None


class UserWithRolesResponse(UserResponse):
    roles: list[str] = Field(default_factory=list)
