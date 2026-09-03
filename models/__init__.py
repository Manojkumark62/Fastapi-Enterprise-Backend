"""
Models package init.

Every model MUST be imported here. SQLAlchemy resolves string-based
relationship() references (e.g. Mapped["Order"]) lazily against its
mapper registry — if a model module is never imported anywhere, its
class never registers, and any OTHER model's relationship() pointing
at it raises `InvalidRequestError: expression ... failed to locate a
name` the first time mappers are configured (typically on first query,
not at import time — which makes forgetting an entry here a
deceptively easy way to ship a bug that only surfaces later).

Order doesn't matter here — SQLAlchemy resolves relationships lazily
regardless of import order — but grouping mirrors the dependency order
they were designed in, for human readability.
"""

from models.user import User
from models.role import Role
from models.permission import Permission
from models.user_role import UserRole
from models.role_permission import RolePermission

from models.employee import Employee
from models.customer import Customer

from models.product import Product
from models.order import Order
from models.order_item import OrderItem
from models.payment import Payment

from models.task import Task
from models.notification import Notification
from models.file import FileRecord
from models.audit_log import AuditLog
from models.record_history import RecordHistory

from models.refresh_token import RefreshToken
from models.session import UserSession
from models.password_reset import PasswordReset
from models.otp import OTP
from models.login_attempt import LoginAttempt

from models.webhook_event import WebhookEvent
from models.report import Report
from models.tenant import Tenant

__all__ = [
    "User",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "Employee",
    "Customer",
    "Product",
    "Order",
    "OrderItem",
    "Payment",
    "Task",
    "Notification",
    "FileRecord",
    "AuditLog",
    "RecordHistory",
    "RefreshToken",
    "UserSession",
    "PasswordReset",
    "OTP",
    "LoginAttempt",
    "WebhookEvent",
    "Report",
    "Tenant",
]
