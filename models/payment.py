"""Payment model — belongs to an Order."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.constants import PaymentStatusEnum
from database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.order import Order


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_payments_amount_nonnegative"),
        CheckConstraint("refunded_amount >= 0", name="ck_payments_refunded_nonnegative"),
        CheckConstraint("refunded_amount <= amount", name="ck_payments_refunded_lte_amount"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True
    )
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=PaymentStatusEnum.PENDING.value, nullable=False, index=True
    )
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)  # card, upi, etc.
    transaction_reference: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    refunded_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    order: Mapped["Order"] = relationship(back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment id={self.id} order_id={self.order_id} status={self.status!r}>"
