import json

from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.constants import WEBHOOK_MAX_RETRIES, WEBHOOK_RETRY_BACKOFF_SECONDS, WebhookStatusEnum
from models.webhook_event import WebhookEvent


def claim_retryable_webhooks(db: Session) -> list[WebhookEvent]:
    events = db.scalars(select(WebhookEvent).where(
        WebhookEvent.status.in_([WebhookStatusEnum.PENDING.value, WebhookStatusEnum.RETRYING.value]),
        WebhookEvent.retry_count < WEBHOOK_MAX_RETRIES,
        (WebhookEvent.next_attempt_at.is_(None) | (WebhookEvent.next_attempt_at <= datetime.now(timezone.utc))),
    ).order_by(WebhookEvent.id).limit(100).with_for_update(skip_locked=True)).all()
    now = datetime.now(timezone.utc)
    for event in events:
        event.status = WebhookStatusEnum.RETRYING.value
        event.retry_count += 1
        event.last_attempted_at = now
    db.commit()
    return events


def mark_webhook_result(db: Session, event: WebhookEvent, delivered: bool, error: str | None = None) -> None:
    event.status = WebhookStatusEnum.DELIVERED.value if delivered else WebhookStatusEnum.FAILED.value
    event.error_message = error
    if not delivered and event.retry_count < WEBHOOK_MAX_RETRIES:
        event.status = WebhookStatusEnum.RETRYING.value
        event.next_attempt_at = datetime.now(timezone.utc) + timedelta(
            seconds=WEBHOOK_RETRY_BACKOFF_SECONDS * (2 ** max(event.retry_count - 1, 0))
        )
    db.commit()