"""
Query filtering helpers for soft-deletes and complex queries.
"""

from sqlalchemy import Select
from sqlalchemy.orm import DeclarativeBase


def exclude_deleted(stmt: Select, model: type[DeclarativeBase]) -> Select:
    """Exclude soft-deleted rows from a query."""
    if hasattr(model, "is_deleted"):
        return stmt.where(model.is_deleted == False)
    return stmt


def with_search(stmt: Select, model: type[DeclarativeBase], search: str | None, fields: list[str]) -> Select:
    """Add full-text-like search across multiple fields."""
    if not search:
        return stmt
    from sqlalchemy import or_
    conditions = [getattr(model, field).ilike(f"%{search}%") for field in fields if hasattr(model, field)]
    if conditions:
        return stmt.where(or_(*conditions))
    return stmt
