"""Task model — assigned to a User, created by an Employee."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.constants import TaskStatusEnum
from database.base import Base, TimestampMixin
from utils.soft_delete_mixin import SoftDeleteMixin

if TYPE_CHECKING:
    from models.user import User
    from models.employee import Employee


class Task(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(20), default=TaskStatusEnum.TODO.value, nullable=False, index=True
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True
    )

    assignee: Mapped["User | None"] = relationship(
        back_populates="assigned_tasks", foreign_keys=[assignee_id]
    )
    created_by: Mapped["Employee | None"] = relationship(
        back_populates="created_tasks", foreign_keys=[created_by_id]
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id} title={self.title!r} status={self.status!r}>"
