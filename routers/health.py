from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from redis import Redis
import httpx

from core.config import settings
from database.session import SessionLocal

router = APIRouter(tags=["Health"])


@router.get("/health/live")
def liveness():
    return {"status": "ok"}


@router.get("/health/ready")
def readiness():
    db = SessionLocal()
    redis_client = Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
    try:
        db.execute(text("SELECT 1"))
        redis_client.ping()
        external = "not_configured"
        if settings.EXTERNAL_HEALTH_URL:
            response = httpx.get(settings.EXTERNAL_HEALTH_URL, timeout=2.0)
            response.raise_for_status()
            external = "ok"
        return {"status": "ready", "database": "ok", "redis": "ok", "external": external}
    except Exception as exc:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            content={"status": "not_ready", "detail": str(exc)[:200]})
    finally:
        db.close()
        redis_client.close()