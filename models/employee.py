"""Employee model — internal staff profile, one-to-one with User."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin
from utils.soft_delete_mixin import SoftDeleteMixin

if TYPE_CHECKING:
    from models.user import User
    from models.task import Task


class Employee(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    employee_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    designation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date_of_joining: Mapped[date | None] = mapped_column(Date, nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    user: Mapped["User"] = relationship(back_populates="employee_profile")
    created_tasks: Mapped[list["Task"]] = relationship(
        back_populates="created_by", foreign_keys="Task.created_by_id"
    )

    def __repr__(self) -> str:
        return f"<Employee id={self.id} code={self.employee_code!r}>"
