"""Product model — catalog entity, referenced by order_items."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin
from utils.soft_delete_mixin import SoftDeleteMixin

if TYPE_CHECKING:
    from models.order_item import OrderItem


class Product(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price > 0", name="ck_products_price_positive"),
        CheckConstraint("stock_quantity >= 0", name="ck_products_stock_nonnegative"),
        Index("ix_products_tenant_category", "tenant_id", "category"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True
    )
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product")

    def __repr__(self) -> str:
        return f"<Product id={self.id} sku={self.sku!r}>"
