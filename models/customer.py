"""Customer model — customer profile, one-to-one with User."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin
from utils.soft_delete_mixin import SoftDeleteMixin

if TYPE_CHECKING:
    from models.user import User
    from models.order import Order


class Customer(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    billing_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    shipping_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    user: Mapped["User"] = relationship(back_populates="customer_profile")
    orders: Mapped[list["Order"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Customer id={self.id} company={self.company_name!r}>"
