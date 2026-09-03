import json
from typing import Any

from redis import Redis

from core.config import settings
from dependencies.tenant import get_current_tenant_id


def tenant_cache_key(key: str) -> str:
    """Namespace cache entries so records cannot cross tenant boundaries."""
    tenant_id = get_current_tenant_id()
    scope = str(tenant_id) if tenant_id is not None else "public"
    return f"tenant:{scope}:{key}"


def get_redis() -> Redis:
    return Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=1)


def cache_get(key: str) -> Any | None:
    client = get_redis()
    try:
        value = client.get(key)
        return json.loads(value) if value else None
    except Exception:
        return None
    finally:
        client.close()


def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    client = get_redis()
    try:
        client.setex(key, ttl or settings.CACHE_DEFAULT_TTL_SECONDS, json.dumps(value, default=str))
    except Exception:
        return
    finally:
        client.close()


def cache_delete(*keys: str) -> None:
    if not keys:
        return
    client = get_redis()
    try:
        client.delete(*keys)
    except Exception:
        return
    finally:
        client.close()


def cache_delete_prefix(prefix: str) -> None:
    client = get_redis()
    try:
        keys = list(client.scan_iter(match=f"{prefix}*"))
        if keys:
            client.delete(*keys)
    except Exception:
        return
    finally:
        client.close()


def temporary_set(key: str, value: Any, ttl: int) -> None:
    """Store short-lived application data; TTL is mandatory."""
    if ttl < 1:
        raise ValueError("ttl must be at least one second")
    cache_set(f"temporary:{tenant_cache_key(key)}", value, ttl=ttl)


def temporary_get(key: str) -> Any | None:
    return cache_get(f"temporary:{tenant_cache_key(key)}")


def temporary_delete(key: str) -> None:
    cache_delete(f"temporary:{tenant_cache_key(key)}")