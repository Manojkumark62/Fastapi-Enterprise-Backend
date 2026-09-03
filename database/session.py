"""
Database engine and session factory.

`get_db()` is the FastAPI dependency every router/service uses to obtain
a session. It's re-exported from app/dependencies/db.py for import
convenience, but the actual engine lives here as the single source of
truth for connection configuration.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from core.config import settings

# pool_pre_ping avoids "MySQL server has gone away" style errors on
# long-lived connections by testing the connection before use.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

_async_url = settings.DATABASE_URL.replace("mysql+pymysql://", "mysql+aiomysql://").replace(
    "postgresql+psycopg://", "postgresql+asyncpg://"
)
async_engine = create_async_engine(_async_url, pool_pre_ping=True, echo=settings.DEBUG)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)


async def get_async_db():
    """Yield an AsyncSession for async API handlers."""
    async with AsyncSessionLocal() as db:
        try:
            yield db
        except Exception:
            await db.rollback()
            raise


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a DB session and guarantees it's
    closed after the request, even if an exception is raised.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
