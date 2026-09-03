"""WebhookEvent model — inbound webhook events + retry state (Modules 45-46)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.constants import WebhookStatusEnum
from database.base import Base, TimestampMixin


class WebhookEvent(Base, TimestampMixin):
    __tablename__ = "webhook_events"
    __table_args__ = (UniqueConstraint("source", "event_id", name="uq_webhook_source_event"),)

    id: Mapped[int] = mapped_column(primary_key=True)

    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # e.g. "stripe"
    event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)  # raw JSON as text

    status: Mapped[str] = mapped_column(
        String(20), default=WebhookStatusEnum.PENDING.value, nullable=False, index=True
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_attempted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    def __repr__(self) -> str:
        return f"<WebhookEvent id={self.id} source={self.source!r} status={self.status!r}>"
