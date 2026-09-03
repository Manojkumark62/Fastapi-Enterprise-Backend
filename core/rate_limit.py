import time
import hashlib

from fastapi import Request
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._fallback_windows = {}

    def _fallback_count(self, key: str) -> int:
        now = time.monotonic()
        window = self._fallback_windows.get(key)
        if window is None or now - window[0] >= 60:
            self._fallback_windows[key] = (now, 1)
            return 1

        count = window[1] + 1
        self._fallback_windows[key] = (window[0], count)
        return count

    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/docs", "/redoc", "/openapi.json", "/swagger"}:
            return await call_next(request)
        client = Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=0.2)
        api_key = request.headers.get("X-API-Key")
        authorization = request.headers.get("Authorization")
        identity = api_key or authorization or (request.client.host if request.client else "unknown")
        identity = hashlib.sha256(identity.encode()).hexdigest()
        key = f"rate:{request.url.path}:{identity}"
        try:
            count = await client.incr(key)
            if count == 1:
                await client.expire(key, 60)
            if count > settings.RATE_LIMIT_PER_MINUTE:
                return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"},
                                    headers={"Retry-After": "60"})
        except Exception:
            count = self._fallback_count(key)
            if count > settings.RATE_LIMIT_PER_MINUTE:
                return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"},
                                    headers={"Retry-After": "60"})
        finally:
            await client.aclose()
        return await call_next(request)