import logging
import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from core.structured_logging import set_request_id
from dependencies.tenant import reset_current_tenant

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        set_request_id(request_id)
        started = time.perf_counter()
        response = None
        try:
            response = await call_next(request)
            elapsed_ms = (time.perf_counter() - started) * 1000
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
            return response
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000
            status_code = response.status_code if response is not None else 500
            logger.info(
                "%s %s status=%s %.2fms request_id=%s",
                request.method,
                request.url.path,
                status_code,
                elapsed_ms,
                request_id,
            )
            set_request_id("")
            reset_current_tenant()