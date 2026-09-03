"""
SQLAlchemy declarative base plus shared mixins used by (almost) every model.

TimestampMixin adds created_at / updated_at to any model that inherits it.
All models import `Base` from here so Alembic's metadata autodiscovery
(see alembic/env.py) sees every table.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    """
    Adds created_at / updated_at columns.
    updated_at auto-refreshes on every UPDATE via onupdate=.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )
