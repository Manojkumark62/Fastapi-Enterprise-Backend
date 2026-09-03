"""One-shot worker entry points; invoke repeatedly from cron or a scheduler."""

from database.session import SessionLocal
from jobs.cleanup import cleanup_expired_security_records
from jobs.webhook_retry import process_webhook_retries
from jobs.scheduled import create_due_task_reminders


def run_maintenance() -> dict:
    db = SessionLocal()
    try:
        cleanup = cleanup_expired_security_records(db)
        webhooks = process_webhook_retries(db)
        reminders = create_due_task_reminders(db)
        return {"cleanup": cleanup, "webhooks": webhooks, "reminders": reminders}
    finally:
        db.close()