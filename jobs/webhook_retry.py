"""Webhook delivery and retry processing."""

import json
import asyncio
from datetime import datetime, timezone, timedelta

import httpx
from sqlalchemy.orm import Session

from core.config import settings
from models.webhook_event import WebhookEvent
from core.constants import WEBHOOK_MAX_RETRIES, WEBHOOK_RETRY_BACKOFF_SECONDS, WebhookStatusEnum


async def deliver_webhook(db: Session, event: WebhookEvent) -> bool:
    """Attempt to deliver a webhook event and update its status."""
    endpoint = settings.WEBHOOK_URLS.get(event.source)
    try:
        payload = json.loads(event.payload)
        if endpoint is None:
            raise ValueError(f"No webhook endpoint configured for source '{event.source}'")

        async with httpx.AsyncClient(timeout=settings.WEBHOOK_TIMEOUT_SECONDS) as client:
            response = await client.post(
                endpoint,
                json=payload,
                headers={"X-Webhook-Event-Type": event.event_type},
            )
            response.raise_for_status()

        event.status = WebhookStatusEnum.DELIVERED.value
        event.error_message = None
        db.commit()
        return True
    except (httpx.HTTPError, ValueError, json.JSONDecodeError) as exc:
        event.status = (
            WebhookStatusEnum.FAILED.value
            if event.retry_count >= WEBHOOK_MAX_RETRIES
            else WebhookStatusEnum.RETRYING.value
        )
        event.error_message = str(exc)[:500]
        event.last_attempted_at = datetime.now(timezone.utc)
        if event.retry_count < WEBHOOK_MAX_RETRIES:
            event.next_attempt_at = datetime.now(timezone.utc) + timedelta(
                seconds=WEBHOOK_RETRY_BACKOFF_SECONDS * (2 ** max(event.retry_count - 1, 0))
            )
        db.commit()
        return False
    except Exception as exc:
        event.status = (
            WebhookStatusEnum.FAILED.value
            if event.retry_count >= WEBHOOK_MAX_RETRIES
            else WebhookStatusEnum.RETRYING.value
        )
        event.error_message = str(exc)[:500]
        event.last_attempted_at = datetime.now(timezone.utc)
        if event.retry_count < WEBHOOK_MAX_RETRIES:
            event.next_attempt_at = datetime.now(timezone.utc) + timedelta(
                seconds=WEBHOOK_RETRY_BACKOFF_SECONDS * (2 ** max(event.retry_count - 1, 0))
            )
        db.commit()
        return False


def process_webhook_retries(db: Session) -> dict:
    """Claim retryable webhooks and attempt delivery."""
    from services.webhook_service import claim_retryable_webhooks
    
    events = claim_retryable_webhooks(db)
    delivered = 0
    failed = 0
    
    async def deliver_batch() -> list[bool | Exception]:
        return await asyncio.gather(
            *(deliver_webhook(db, event) for event in events),
            return_exceptions=True,
        )

    results = asyncio.run(deliver_batch())
    for event, result in zip(events, results):
        if isinstance(result, Exception):
            event.status = (
                WebhookStatusEnum.FAILED.value
                if event.retry_count >= WEBHOOK_MAX_RETRIES
                else WebhookStatusEnum.RETRYING.value
            )
            event.error_message = str(result)[:500]
            db.commit()
            failed += 1
        elif result:
            delivered += 1
        else:
            failed += 1
    
    return {"delivered": delivered, "failed": failed, "total": len(events)}
