from pydantic import BaseModel, ConfigDict, Field


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    description: str | None


class PermissionCreateRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)
