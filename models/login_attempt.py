"""
LoginAttempt model — failed-login tracking and account locking (Module 28).

A persisted table (rather than an in-memory counter) so lockout state
survives process restarts and is auditable.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.user import User


class LoginAttempt(Base, TimestampMixin):
    __tablename__ = "login_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    was_successful: Mapped[bool] = mapped_column(Boolean, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="login_attempts")

    def __repr__(self) -> str:
        return f"<LoginAttempt id={self.id} user_id={self.user_id} success={self.was_successful}>"
