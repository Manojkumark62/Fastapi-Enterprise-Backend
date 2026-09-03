"""
Shared query-filter helpers (Module 17/19).

exclude_deleted() is applied by every service that queries a
SoftDeleteMixin model, so "don't show soft-deleted rows" is enforced
consistently rather than trusted to each service author to remember.
"""

from sqlalchemy import Select


def exclude_deleted(stmt: Select, model) -> Select:
    """
    Adds `WHERE is_deleted = False` to a select statement, for any model
    that inherits SoftDeleteMixin. Safe to call even if the model has no
    such column — callers should only invoke this on models that do.
    """
    return stmt.where(model.is_deleted == False)  # noqa: E712 — SQLAlchemy requires == here


def apply_sort(stmt: Select, model, sort_by: str | None, sort_order: str = "asc") -> Select:
    """
    Applies ORDER BY sort_by [ASC|DESC] if sort_by names a real column on
    the model. Silently ignores unknown column names rather than raising,
    since sort_by typically comes straight from a query parameter and a
    typo shouldn't 500 the request.
    """
    if sort_by is None or not hasattr(model, sort_by):
        return stmt

    column = getattr(model, sort_by)
    return stmt.order_by(column.desc() if sort_order.lower() == "desc" else column.asc())
