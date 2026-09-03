"""
OTP model — one-time passcodes (Module 29).

Kept separate from PasswordReset: OTP here is a general-purpose
verification mechanism (password recovery today, potentially 2FA or
email verification later) rather than being conflated into the
password-reset flow specifically.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.user import User


class OTP(Base, TimestampMixin):
    __tablename__ = "otps"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)  # never store OTP in plaintext
    purpose: Mapped[str] = mapped_column(String(50), nullable=False)  # "password_reset", "2fa", etc.
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    attempt_count: Mapped[int] = mapped_column(default=0, nullable=False)

    user: Mapped["User"] = relationship(back_populates="otps")

    def __repr__(self) -> str:
        return f"<OTP id={self.id} user_id={self.user_id} purpose={self.purpose!r}>"
