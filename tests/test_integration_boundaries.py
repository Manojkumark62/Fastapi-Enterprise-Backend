import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from core.config import settings
from core.cache import temporary_set
from services.enterprise_service import EnterpriseService
from services import external_api_service
from services.webhook_service import mark_webhook_result


class _Db:
    def __init__(self, existing=None):
        self.existing = existing
        self.added = []

    def scalar(self, _statement):
        return self.existing

    def add(self, value):
        self.added.append(value)

    def commit(self):
        return None

    def flush(self):
        return None

    def refresh(self, _value):
        return None


def test_webhook_uses_raw_body_and_deduplicates(monkeypatch):
    settings.WEBHOOK_SECRETS = {"test": "secret"}
    raw = b'{"z":1,"a":2}'
    timestamp = int(time.time())
    signature = hmac.new(b"secret", str(timestamp).encode() + b"." + raw, hashlib.sha256).hexdigest()
    event = EnterpriseService(_Db()).receive_webhook("test", "created", raw, signature, "evt-1", timestamp)
    assert event.event_id == "evt-1"
    duplicate = EnterpriseService(_Db(existing=event)).receive_webhook(
        "test", "created", raw, signature, "evt-1", timestamp
    )
    assert duplicate is event


def test_webhook_retry_sets_backoff():
    event = SimpleNamespace(retry_count=2, status="retrying", error_message=None, next_attempt_at=None)
    db = _Db()
    mark_webhook_result(db, event, delivered=False, error="timeout")
    assert event.status == "retrying"
    assert event.next_attempt_at is not None


def test_webhook_accepts_millisecond_timestamp():
    settings.WEBHOOK_SECRETS = {"test": "secret"}
    raw = b'{"ok":true}'
    timestamp = int(time.time())
    millisecond_timestamp = timestamp * 1000
    signature = hmac.new(
        b"secret",
        f"{millisecond_timestamp}.".encode() + raw,
        hashlib.sha256,
    ).hexdigest()

    event = EnterpriseService(_Db()).receive_webhook(
        "test", "created", raw, signature, "evt-ms", millisecond_timestamp
    )

    assert event.event_id == "evt-ms"


def test_webhook_accepts_iso_timestamp():
    settings.WEBHOOK_SECRETS = {"test": "secret"}
    raw = b'{"ok":true}'
    iso_timestamp = datetime.now(timezone.utc).isoformat()
    signature = hmac.new(
        b"secret",
        f"{iso_timestamp}.".encode() + raw,
        hashlib.sha256,
    ).hexdigest()

    event = EnterpriseService(_Db()).receive_webhook(
        "test", "created", raw, signature, "evt-iso", iso_timestamp
    )

    assert event.event_id == "evt-iso"


@pytest.mark.asyncio
async def test_external_response_is_transformed(monkeypatch):
    class ResponseModel(external_api_service.BaseModel):
        name: str

    async def fake_fetch_json(*_args, **_kwargs):
        return {"name": "provider"}

    monkeypatch.setattr(external_api_service, "fetch_json", fake_fetch_json)
    result = await external_api_service.fetch_and_transform("https://example.test", ResponseModel)
    assert result.name == "provider"


def test_temporary_cache_requires_positive_ttl():
    with pytest.raises(ValueError):
        temporary_set("key", {"value": 1}, ttl=0)
