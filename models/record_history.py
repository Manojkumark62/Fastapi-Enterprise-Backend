"""
RecordHistory model — previous versions of records (Module 40).

Uses a generic entity_type/entity_id pair rather than a foreign key per
model. This is a deliberate trade-off: it means no DB-level referential
integrity for history rows (a service-layer concern instead), but it
avoids needing a new history table for every versioned entity. Given the
number of versionable entities in this app (orders, products, users,
etc.), the generic approach scales far better than one history table
per entity.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.user import User


class RecordHistory(Base, TimestampMixin):
    __tablename__ = "record_history"

    id: Mapped[int] = mapped_column(primary_key=True)

    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Full snapshot of the record's state at this point in time, as JSON text.
    snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    change_type: Mapped[str] = mapped_column(String(20), nullable=False)  # created/updated/deleted

    changed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    changed_by: Mapped["User | None"] = relationship()

    def __repr__(self) -> str:
        return f"<RecordHistory id={self.id} entity={self.entity_type}#{self.entity_id}>"
