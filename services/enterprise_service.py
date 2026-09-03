import csv
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.config import settings
from core.constants import TaskStatusEnum, WebhookStatusEnum
from models.audit_log import AuditLog
from models.file import FileRecord
from models.notification import Notification
from models.record_history import RecordHistory
from models.report import Report
from models.task import Task
from models.user import User
from models.webhook_event import WebhookEvent
from core.security import hash_password
from dependencies.tenant import get_required_tenant_id
from schemas.auth import UserRegisterRequest


def add_audit_log(db: Session, actor_id: int | None, action: str, entity_type: str,
                  entity_id: int | None, description: str | None = None,
                  ip_address: str | None = None) -> AuditLog:
    log = AuditLog(actor_id=actor_id, action=action, entity_type=entity_type,
                   entity_id=entity_id, description=description, ip_address=ip_address)
    db.add(log)
    return log


def add_history(db: Session, entity_type: str, entity_id: int, snapshot: object,
                change_type: str, changed_by_id: int | None) -> RecordHistory:
    history = RecordHistory(entity_type=entity_type, entity_id=entity_id,
                            snapshot=json.dumps(snapshot, default=str),
                            change_type=change_type, changed_by_id=changed_by_id)
    db.add(history)
    return history


class EnterpriseService:
    def __init__(self, db: Session):
        self.db = db

    def create_task(self, data: dict, actor: User) -> Task:
        if data.get("assignee_id") is not None and self.db.get(User, data["assignee_id"]) is None:
            raise ValueError("Assignee not found")
        task = Task(
            **data,
            tenant_id=get_required_tenant_id(),
            created_by_id=actor.employee_profile.id if actor.employee_profile else None,
        )
        self.db.add(task)
        self.db.flush()
        self.db.commit()
        self.db.refresh(task)
        return task

    def update_task(self, task_id: int, data: dict, actor: User) -> Task | None:
        task = self.db.scalar(select(Task).where(
            Task.id == task_id,
            Task.tenant_id == get_required_tenant_id(),
            Task.is_deleted.is_(False),
        ))
        if task is None:
            return None
        if data.get("assignee_id") is not None and self.db.get(User, data["assignee_id"]) is None:
            raise ValueError("Assignee not found")
        for key, value in data.items():
            if value is not None:
                setattr(task, key, value)
        self.db.commit()
        self.db.refresh(task)
        return task

    def save_upload(self, upload: UploadFile, actor: User) -> FileRecord:
        safe_name = Path(upload.filename or "upload.bin").name
        content = upload.file.read(settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024 + 1)
        if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            raise ValueError("File exceeds the configured size limit")
        directory = Path(settings.UPLOAD_DIR)
        directory.mkdir(parents=True, exist_ok=True)
        stored_name = f"{secrets.token_urlsafe(18)}-{safe_name}"
        path = directory / stored_name
        path.write_bytes(content)
        record = FileRecord(uploaded_by_id=actor.id, original_filename=safe_name,
                            stored_filename=stored_name, content_type=upload.content_type,
                            size_bytes=len(content), storage_path=str(path))
        self.db.add(record)
        self.db.flush()
        self.db.commit()
        self.db.refresh(record)
        return record

    def delete_file(self, file_id: int, actor: User) -> bool:
        record = self.db.scalar(select(FileRecord).where(FileRecord.id == file_id,
                                                         FileRecord.uploaded_by_id == actor.id,
                                                         FileRecord.is_deleted.is_(False)))
        if record is None:
            return False
        record.soft_delete()
        path = Path(record.storage_path)
        if path.is_file():
            path.unlink()
        self.db.commit()
        return True

    def update_file(self, file_id: int, data: dict, actor: User) -> FileRecord | None:
        record = self.db.scalar(select(FileRecord).where(
            FileRecord.id == file_id,
            FileRecord.uploaded_by_id == actor.id,
            FileRecord.is_deleted.is_(False),
        ))
        if record is None:
            return None
        if data.get("original_filename") is not None:
            record.original_filename = Path(data["original_filename"]).name
        self.db.commit()
        self.db.refresh(record)
        return record

    def import_users(self, content: str, actor: User) -> dict:
        reader = csv.DictReader(StringIO(content))
        required = {"email", "full_name", "password"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("CSV must contain email, full_name, and password columns")
        succeeded = 0
        errors = []
        for line_number, row in enumerate(reader, start=2):
            with self.db.begin_nested():
                try:
                    payload = UserRegisterRequest(**row)
                    if self.db.scalar(select(User).where(User.email == payload.email)) is not None:
                        raise ValueError("email already exists")
                    user = User(email=str(payload.email), full_name=payload.full_name,
                                hashed_password=hash_password(payload.password))
                    self.db.add(user)
                    self.db.flush()
                    add_audit_log(self.db, actor.id, "USER_IMPORTED", "User", user.id)
                    succeeded += 1
                except Exception as exc:
                    errors.append(f"line {line_number}: {exc}")
        self.db.commit()
        return {"succeeded": succeeded, "failed": len(errors), "errors": errors}

    def create_report(
        self, actor: User, search: str | None = None, is_active: bool | None = None
    ) -> tuple[Report, str]:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "email", "full_name", "is_active", "created_at"])
        query = select(User).where(User.is_deleted.is_(False))
        if search:
            query = query.where(User.full_name.ilike(f"%{search}%") | User.email.ilike(f"%{search}%"))
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        for user in self.db.scalars(query.order_by(User.id)).all():
            writer.writerow([user.id, user.email, user.full_name, user.is_active, user.created_at.isoformat()])
        report = Report(name="User export", report_type="users_csv", generated_by_id=actor.id,
                parameters=json.dumps({"search": search, "is_active": is_active}), status="completed")
        self.db.add(report)
        self.db.flush()
        directory = Path(settings.UPLOAD_DIR)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"report-{report.id}.csv"
        path.write_text(output.getvalue(), encoding="utf-8")
        report.result_file_path = str(path)
        add_audit_log(self.db, actor.id, "REPORT_GENERATED", "Report", report.id)
        self.db.commit()
        self.db.refresh(report)
        return report, output.getvalue()

    def receive_webhook(self, source: str, event_type: str, raw: bytes,
                        signature: str | None, event_id: str, timestamp: str | int) -> WebhookEvent:
        # Accept Unix seconds, Unix milliseconds, or an ISO-8601 timestamp.
        signed_timestamp = str(timestamp).strip()
        try:
            if signed_timestamp.lstrip("+-").isdigit():
                numeric_timestamp = int(signed_timestamp)
                timestamp_seconds = (
                    numeric_timestamp // 1000
                    if numeric_timestamp > 10_000_000_000
                    else numeric_timestamp
                )
            else:
                timestamp_value = datetime.fromisoformat(signed_timestamp.replace("Z", "+00:00"))
                if timestamp_value.tzinfo is None:
                    timestamp_value = timestamp_value.replace(tzinfo=timezone.utc)
                timestamp_seconds = int(timestamp_value.timestamp())
        except (TypeError, ValueError) as exc:
            raise PermissionError(
                "Invalid webhook timestamp; use current Unix seconds, milliseconds, or ISO-8601"
            ) from exc

        current_timestamp = int(datetime.now(timezone.utc).timestamp())
        if abs(current_timestamp - timestamp_seconds) > settings.WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS:
            raise PermissionError(
                f"Webhook timestamp expired; it must be within "
                f"{settings.WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS} seconds of server time"
            )
        secret = settings.WEBHOOK_SECRETS.get(source)
        if not secret:
            raise PermissionError("Webhook source is not configured")
        signed = f"{signed_timestamp}.".encode() + raw
        expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
        # Keep compatibility with integrations that sign normalized seconds.
        legacy_signed = f"{timestamp_seconds}.".encode() + raw
        legacy_expected = hmac.new(secret.encode(), legacy_signed, hashlib.sha256).hexdigest()
        provided_signature = signature.removeprefix("sha256=") if signature else ""
        if not signature or not any(
            hmac.compare_digest(candidate, provided_signature)
            for candidate in (expected, legacy_expected)
        ):
            raise PermissionError("Invalid webhook signature")
        existing = self.db.scalar(select(WebhookEvent).where(
            WebhookEvent.source == source, WebhookEvent.event_id == event_id
        ))
        if existing is not None:
            return existing
        event = WebhookEvent(source=source, event_id=event_id, event_type=event_type, payload=raw.decode("utf-8"),
                             status=WebhookStatusEnum.PENDING.value)
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event