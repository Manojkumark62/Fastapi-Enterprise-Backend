from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    assignee_id: int | None = None
    due_date: date | None = None


class TaskUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = None
    assignee_id: int | None = None
    due_date: date | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str | None
    status: str
    assignee_id: int | None
    created_by_id: int | None
    due_date: date | None
    created_at: datetime


class NotificationCreateRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    notification_type: str = "info"


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    actor_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    description: str | None
    ip_address: str | None
    created_at: datetime


class RecordHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    entity_type: str
    entity_id: int
    snapshot: str
    change_type: str
    changed_by_id: int | None
    created_at: datetime


class WebhookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source: str
    event_type: str
    status: str
    retry_count: int
    error_message: str | None
    created_at: datetime


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    report_type: str
    generated_by_id: int | None
    parameters: str | None
    result_file_path: str | None
    status: str
    created_at: datetime


class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    original_filename: str
    content_type: str | None
    size_bytes: int
    created_at: datetime


class FileUpdateRequest(BaseModel):
    original_filename: str | None = Field(default=None, min_length=1, max_length=255)


class ImportResult(BaseModel):
    succeeded: int
    failed: int
    errors: list[str] = []