from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class EmployeeCreateRequest(BaseModel):
    user_id: int
    employee_code: str = Field(..., min_length=1, max_length=50)
    department: str | None = Field(default=None, max_length=100)
    designation: str | None = Field(default=None, max_length=100)
    date_of_joining: date | None = None
    phone_number: str | None = Field(default=None, max_length=20)


class EmployeeUpdateRequest(BaseModel):
    department: str | None = Field(default=None, max_length=100)
    designation: str | None = Field(default=None, max_length=100)
    phone_number: str | None = Field(default=None, max_length=20)


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    employee_code: str
    department: str | None
    designation: str | None
    date_of_joining: date | None
    phone_number: str | None
    created_at: datetime
