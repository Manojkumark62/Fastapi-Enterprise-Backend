"""OrderItem model — line item joining Order and Product, with price snapshot."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.order import Order
    from models.product import Product


class OrderItem(Base, TimestampMixin):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_order_items_unit_price_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Snapshot the price at time of purchase — product.price may change later,
    # but this order line must always reflect what was actually charged.
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="order_items")

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity

    def __repr__(self) -> str:
        return f"<OrderItem id={self.id} order_id={self.order_id} product_id={self.product_id}>"
