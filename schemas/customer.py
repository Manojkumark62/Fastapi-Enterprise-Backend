from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CustomerCreateRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    company_name: str | None = Field(default=None, max_length=255)
    billing_address: str | None = Field(default=None, max_length=500)
    shipping_address: str | None = Field(default=None, max_length=500)
    phone_number: str | None = Field(default=None, max_length=20)


class CustomerUpdateRequest(BaseModel):
    company_name: str | None = Field(default=None, max_length=255)
    billing_address: str | None = Field(default=None, max_length=500)
    shipping_address: str | None = Field(default=None, max_length=500)
    phone_number: str | None = Field(default=None, max_length=20)


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    company_name: str | None
    billing_address: str | None
    shipping_address: str | None
    phone_number: str | None
    created_at: datetime
