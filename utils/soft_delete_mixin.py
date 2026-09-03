"""
Soft-delete mixin (Module 19).

Any model that inherits this gets `is_deleted` / `deleted_at` columns
instead of being physically removed from the table on delete. Pair
with `query_filters.py`'s `exclude_deleted()` helper in service-layer
queries so soft-deleted rows don't silently reappear in listings.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column


class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def soft_delete(self) -> None:
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        self.is_deleted = False
        self.deleted_at = None
