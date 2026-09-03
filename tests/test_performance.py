import asyncio
import time

import httpx
import pytest

from main import app


@pytest.mark.asyncio
async def test_liveness_handles_concurrent_requests():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        started = time.perf_counter()
        responses = await asyncio.gather(
            *(client.get("/health/live", headers={"X-API-Key": f"perf-{index}"}) for index in range(25))
        )
        elapsed = time.perf_counter() - started

    assert all(response.status_code == 200 for response in responses)
    assert elapsed < 5
