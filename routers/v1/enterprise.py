from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, Header, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect, status
from fastapi.responses import FileResponse as DownloadResponse, StreamingResponse
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.constants import TaskStatusEnum
from core.config import settings
from core.security import decode_token
from dependencies.auth import get_current_active_user
from dependencies.tenant import get_required_tenant_id
from database.session import AsyncSessionLocal
from dependencies.db import get_db
from models.audit_log import AuditLog
from models.file import FileRecord
from models.notification import Notification
from models.record_history import RecordHistory
from models.task import Task
from models.user import User
from schemas.enterprise import (AuditLogResponse, FileResponse, FileUpdateRequest, ImportResult, NotificationCreateRequest,
    NotificationResponse, RecordHistoryResponse, ReportResponse, TaskCreateRequest,
    TaskResponse, TaskUpdateRequest, WebhookResponse)
from services.enterprise_service import EnterpriseService, add_audit_log
from services.notification_manager import notification_manager
from services.webhook_service import claim_retryable_webhooks

router = APIRouter(tags=["Enterprise features"])


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreateRequest, db: Session = Depends(get_db), actor: User = Depends(get_current_active_user)):
    try:
        return EnterpriseService(db).create_task(payload.model_dump(), actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/tasks", response_model=list[TaskResponse])
def list_tasks(db: Session = Depends(get_db), _: User = Depends(get_current_active_user)):
    return db.scalars(select(Task).where(
        Task.tenant_id == get_required_tenant_id(),
        Task.is_deleted.is_(False),
    ).order_by(Task.id.desc())).all()


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, payload: TaskUpdateRequest, db: Session = Depends(get_db), actor: User = Depends(get_current_active_user)):
    if payload.status is not None and payload.status not in {item.value for item in TaskStatusEnum}:
        raise HTTPException(status_code=422, detail="Invalid task status")
    try:
        task = EnterpriseService(db).update_task(task_id, payload.model_dump(exclude_unset=True), actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/tasks/{task_id}", response_model=TaskResponse)
def replace_task(task_id: int, payload: TaskUpdateRequest, db: Session = Depends(get_db), actor: User = Depends(get_current_active_user)):
    if payload.status is not None and payload.status not in {item.value for item in TaskStatusEnum}:
        raise HTTPException(status_code=422, detail="Invalid task status")
    try:
        task = EnterpriseService(db).update_task(task_id, payload.model_dump(exclude_unset=True), actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/notifications", response_model=NotificationResponse, status_code=201)
def create_notification(payload: NotificationCreateRequest, background_tasks: BackgroundTasks,
                        db: Session = Depends(get_db), actor: User = Depends(get_current_active_user)):
    if payload.user_id != actor.id and not actor.is_superuser:
        raise HTTPException(status_code=403, detail="You cannot create notifications for another user")
    if db.get(User, payload.user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    notification = Notification(**payload.model_dump())
    db.add(notification)
    db.flush()
    add_audit_log(db, actor.id, "NOTIFICATION_CREATED", "Notification", notification.id)
    db.commit()
    db.refresh(notification)
    background_tasks.add_task(
        notification_manager.broadcast,
        notification.user_id,
        NotificationResponse.model_validate(notification).model_dump(mode="json"),
    )
    return notification


@router.websocket("/ws/notifications")
async def notification_stream(websocket: WebSocket, token: str):
    """Stream notifications to the authenticated user over WebSocket."""
    user_id: int | None = None
    async with AsyncSessionLocal() as db:
      try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            await websocket.close(code=1008)
            return
        user_id = int(payload["sub"])
        user = await db.scalar(select(User).where(User.id == user_id))
        if user is None or user.is_deleted or not user.is_active:
            await websocket.close(code=1008)
            return
        await notification_manager.connect(user_id, websocket)
        while True:
            await websocket.receive_text()
      except (JWTError, KeyError, TypeError, ValueError):
        await websocket.close(code=1008)
      except WebSocketDisconnect:
        pass
      finally:
        if user_id is not None:
            notification_manager.disconnect(user_id, websocket)


@router.get("/notifications", response_model=list[NotificationResponse])
def list_notifications(
    is_read: bool | None = None,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_active_user),
):
    query = select(Notification).where(Notification.user_id == actor.id)
    if is_read is not None:
        query = query.where(Notification.is_read == is_read)
    return db.scalars(query.order_by(Notification.id.desc())).all()


@router.patch("/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(notification_id: int, db: Session = Depends(get_db), actor: User = Depends(get_current_active_user)):
    notification = db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == actor.id))
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


@router.patch("/notifications/{notification_id}/unread", response_model=NotificationResponse)
def mark_notification_unread(notification_id: int, db: Session = Depends(get_db), actor: User = Depends(get_current_active_user)):
    notification = db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == actor.id))
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = False
    db.commit()
    db.refresh(notification)
    return notification


@router.get("/notifications/history", response_model=list[NotificationResponse])
def notification_history(db: Session = Depends(get_db), actor: User = Depends(get_current_active_user)):
    return db.scalars(select(Notification).where(Notification.user_id == actor.id).order_by(Notification.created_at.desc())).all()


@router.post("/files", response_model=FileResponse, status_code=201)
def upload_file(upload: UploadFile = File(...), db: Session = Depends(get_db), actor: User = Depends(get_current_active_user)):
    try:
        return EnterpriseService(db).save_upload(upload, actor)
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc


@router.get("/files/{file_id}/download")
def download_file(file_id: int, db: Session = Depends(get_db), actor: User = Depends(get_current_active_user)):
    record = db.scalar(select(FileRecord).where(
        FileRecord.id == file_id,
        FileRecord.uploaded_by_id == actor.id,
        FileRecord.is_deleted.is_(False),
    ))
    if record is None or not Path(record.storage_path).is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return DownloadResponse(record.storage_path, filename=record.original_filename, media_type=record.content_type)


@router.patch("/files/{file_id}", response_model=FileResponse)
def update_file(file_id: int, payload: FileUpdateRequest, db: Session = Depends(get_db), actor: User = Depends(get_current_active_user)):
    record = EnterpriseService(db).update_file(file_id, payload.model_dump(exclude_unset=True), actor)
    if record is None:
        raise HTTPException(status_code=404, detail="File not found")
    return record


@router.put("/files/{file_id}", response_model=FileResponse)
def replace_file(file_id: int, payload: FileUpdateRequest, db: Session = Depends(get_db), actor: User = Depends(get_current_active_user)):
    record = EnterpriseService(db).update_file(file_id, payload.model_dump(exclude_unset=True), actor)
    if record is None:
        raise HTTPException(status_code=404, detail="File not found")
    return record


@router.get("/files", response_model=list[FileResponse])
def list_files(db: Session = Depends(get_db), actor: User = Depends(get_current_active_user)):
    return db.scalars(select(FileRecord).where(FileRecord.uploaded_by_id == actor.id,
                                               FileRecord.is_deleted.is_(False)).order_by(FileRecord.id.desc())).all()


@router.delete("/files/{file_id}", status_code=204)
def delete_file(file_id: int, db: Session = Depends(get_db), actor: User = Depends(get_current_active_user)):
    if not EnterpriseService(db).delete_file(file_id, actor):
        raise HTTPException(status_code=404, detail="File not found")


@router.post("/imports/users", response_model=ImportResult)
def import_users(upload: UploadFile = File(...), db: Session = Depends(get_db), actor: User = Depends(get_current_active_user)):
    if upload.content_type not in {"text/csv", "application/csv", "application/vnd.ms-excel"}:
        raise HTTPException(status_code=415, detail="A CSV file is required")
    try:
        content = upload.file.read(settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024 + 1)
        if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            raise ValueError("File exceeds the configured size limit")
        return EnterpriseService(db).import_users(content.decode("utf-8-sig"), actor)
    except (UnicodeDecodeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/audit-logs", response_model=list[AuditLogResponse])
def list_audit_logs(db: Session = Depends(get_db), _: User = Depends(get_current_active_user)):
    return db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(100)).all()


@router.get("/history/{entity_type}/{entity_id}", response_model=list[RecordHistoryResponse])
def list_history(entity_type: str, entity_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)):
    return db.scalars(select(RecordHistory).where(RecordHistory.entity_type == entity_type, RecordHistory.entity_id == entity_id).order_by(RecordHistory.id.desc())).all()


@router.post("/reports/users.csv")
def export_users(search: str | None = None, is_active: bool | None = None, db: Session = Depends(get_db), actor: User = Depends(get_current_active_user)):
    _, content = EnterpriseService(db).create_report(actor, search=search, is_active=is_active)
    return StreamingResponse(iter([content]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=users.csv"})


@router.post(
    "/webhooks/{source}/{event_type}",
    response_model=WebhookResponse,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"type": "object"},
                    "example": {
                        "transaction_id": "txn-1001",
                        "amount": 799.0,
                        "currency": "INR",
                        "status": "success",
                    },
                }
            },
        }
    },
)
async def receive_webhook(source: str, event_type: str, request: Request, db: Session = Depends(get_db),
                          x_signature: str | None = Header(default=None),
                          x_event_id: str = Header(...), x_webhook_timestamp: str = Header(...)):
    try:
        return EnterpriseService(db).receive_webhook(
            source, event_type, await request.body(), x_signature, x_event_id, x_webhook_timestamp
        )
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/webhooks/retry", response_model=list[WebhookResponse])
def retry_webhooks(db: Session = Depends(get_db), _: User = Depends(get_current_active_user)):
    return claim_retryable_webhooks(db)