"""Order model — belongs to a Customer, contains OrderItems, has Payments."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.constants import OrderStatusEnum
from database.base import Base, TimestampMixin
from utils.soft_delete_mixin import SoftDeleteMixin

if TYPE_CHECKING:
    from models.customer import Customer
    from models.order_item import OrderItem
    from models.payment import Payment


class Order(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="ck_orders_total_nonnegative"),
        Index("ix_orders_tenant_status_created", "tenant_id", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True
    )
    order_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    status: Mapped[str] = mapped_column(
        String(20), default=OrderStatusEnum.PENDING.value, nullable=False, index=True
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    shipping_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    customer: Mapped["Customer"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Order id={self.id} number={self.order_number!r} status={self.status!r}>"
