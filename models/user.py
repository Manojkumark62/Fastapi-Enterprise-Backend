"""User model — the root authentication entity."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin
from utils.soft_delete_mixin import SoftDeleteMixin

if TYPE_CHECKING:
    from models.user_role import UserRole
    from models.employee import Employee
    from models.customer import Customer
    from models.refresh_token import RefreshToken
    from models.session import UserSession
    from models.notification import Notification
    from models.audit_log import AuditLog
    from models.file import FileRecord
    from models.password_reset import PasswordReset
    from models.otp import OTP
    from models.login_attempt import LoginAttempt
    from models.task import Task


class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- Relationships ---
    user_roles: Mapped[list["UserRole"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    employee_profile: Mapped["Employee | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    customer_profile: Mapped["Customer | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="actor")
    files: Mapped[list["FileRecord"]] = relationship(
        back_populates="uploaded_by", cascade="all, delete-orphan"
    )
    password_resets: Mapped[list["PasswordReset"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    otps: Mapped[list["OTP"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    login_attempts: Mapped[list["LoginAttempt"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    assigned_tasks: Mapped[list["Task"]] = relationship(
        back_populates="assignee", foreign_keys="Task.assignee_id"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
