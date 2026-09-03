"""
Fixed values shared across the application: roles, statuses, limits.

Centralizing these avoids magic strings scattered through models,
schemas, and services, and makes renames a one-file change.
"""

from enum import Enum


class UserRoleEnum(str, Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    USER = "USER"


class PermissionCodeEnum(str, Enum):
    CREATE_USER = "CREATE_USER"
    UPDATE_USER = "UPDATE_USER"
    DELETE_USER = "DELETE_USER"
    VIEW_USER = "VIEW_USER"

    CREATE_PRODUCT = "CREATE_PRODUCT"
    UPDATE_PRODUCT = "UPDATE_PRODUCT"
    DELETE_PRODUCT = "DELETE_PRODUCT"

    CREATE_ORDER = "CREATE_ORDER"
    UPDATE_ORDER = "UPDATE_ORDER"
    DELETE_ORDER = "DELETE_ORDER"
    VIEW_ORDER = "VIEW_ORDER"

    VIEW_AUDIT_LOG = "VIEW_AUDIT_LOG"
    VIEW_REPORT = "VIEW_REPORT"
    MANAGE_ROLES = "MANAGE_ROLES"


class OrderStatusEnum(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatusEnum(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


class TaskStatusEnum(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class NotificationTypeEnum(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class WebhookStatusEnum(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


# --- Pagination ---
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# --- Account security ---
MAX_LOGIN_ATTEMPTS = 5
ACCOUNT_LOCK_DURATION_MINUTES = 15

# --- OTP ---
OTP_LENGTH = 6
OTP_EXPIRE_MINUTES = 10

# --- Webhook retry ---
WEBHOOK_MAX_RETRIES = 5
WEBHOOK_RETRY_BACKOFF_SECONDS = 60
