"""
Re-exports get_db from database/session.py.

Routers and other dependencies import `Depends(get_db)` from here rather
than from app.database.session directly, so all FastAPI-facing
dependencies live under one package.
"""

from database.session import get_async_db, get_db

__all__ = ["get_db", "get_async_db"]

__all__ = ["get_db"]
