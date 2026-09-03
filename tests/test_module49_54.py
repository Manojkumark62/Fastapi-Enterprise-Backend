import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from core.security import create_access_token, decode_token, hash_password, verify_password
from jobs import webhook_retry
from routers import health
from services import external_api_service


@pytest.mark.asyncio
async def test_webhook_batch_runs_independent_operations_concurrently(monkeypatch):
    events = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
    started = 0
    peak = 0

    async def deliver(_db, _event):
        nonlocal started, peak
        started += 1
        peak = max(peak, started)
        await asyncio.sleep(0)
        started -= 1
        return True

    monkeypatch.setattr(webhook_retry, "deliver_webhook", deliver)
    monkeypatch.setattr(webhook_retry, "WEBHOOK_MAX_RETRIES", 5)
    db = Mock()
    monkeypatch.setattr("services.webhook_service.claim_retryable_webhooks", lambda _db: events)
    result = await asyncio.to_thread(webhook_retry.process_webhook_retries, db)
    assert result == {"delivered": 2, "failed": 0, "total": 2}
    assert peak == 2


def test_authentication_primitives():
    hashed = hash_password("StrongPass1!")
    assert verify_password("StrongPass1!", hashed)
    assert not verify_password("wrong", hashed)
    assert decode_token(create_access_token("42"))["sub"] == "42"


@pytest.mark.asyncio
async def test_external_api_errors_are_translated(monkeypatch):
    class Response:
        def raise_for_status(self):
            raise external_api_service.httpx.TimeoutException("timeout")

        def json(self):
            return {}

    client = AsyncMock()
    client.__aenter__.return_value.get.return_value = Response()
    monkeypatch.setattr(external_api_service.httpx, "AsyncClient", Mock(return_value=client))
    with pytest.raises(external_api_service.ExternalAPIError):
        await external_api_service.fetch_json("https://example.test")


def test_readiness_reports_dependency_failure(monkeypatch):
    class BrokenSession:
        def execute(self, _statement):
            raise RuntimeError("database unavailable")

        def close(self):
            pass

    monkeypatch.setattr(health, "SessionLocal", lambda: BrokenSession())
    response = health.readiness()
    assert response.status_code == 503
    assert response.body == b'{"status":"not_ready","detail":"database unavailable"}'
