"""AuditLog model — tracks important actions across the app (Module 39)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.user import User


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Nullable: some actions are system-initiated (scheduled jobs, webhooks)
    # and have no human actor.
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # e.g. "USER_UPDATED"
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # e.g. "User"
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)

    actor: Mapped["User | None"] = relationship(back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action={self.action!r} entity={self.entity_type}#{self.entity_id}>"
