"""Notification model — belongs to a User."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.constants import NotificationTypeEnum
from database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.user import User


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_read_created", "user_id", "is_read", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(
        String(20), default=NotificationTypeEnum.INFO.value, nullable=False
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    user: Mapped["User"] = relationship(back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification id={self.id} user_id={self.user_id} read={self.is_read}>"
