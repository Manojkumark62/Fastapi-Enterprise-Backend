"""
Custom exceptions for authentication and authorization failures.

Kept as plain Python exceptions (not HTTPException subclasses) so the
service layer stays framework-agnostic — routers/dependencies catch
these and translate to the appropriate HTTP response. This also means
these exceptions are testable without spinning up FastAPI at all.
"""


class AppException(Exception):
    """Base class for all custom application exceptions."""

    status_code = 400

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        super().__init__(message)


# --- Authentication ---

class InvalidCredentialsError(AppException):
    """Wrong email or password at login."""

    status_code = 401

    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message)


class AccountLockedError(AppException):
    """Account temporarily locked after too many failed login attempts."""

    status_code = 423

    def __init__(self, message: str = "Account is temporarily locked due to too many failed attempts"):
        super().__init__(message)


class AccountInactiveError(AppException):
    """Account exists but is deactivated."""

    status_code = 403

    def __init__(self, message: str = "This account has been deactivated"):
        super().__init__(message)


class EmailAlreadyRegisteredError(AppException):
    """Registration attempted with an email that's already in use."""

    def __init__(self, message: str = "An account with this email already exists"):
        super().__init__(message)


class DuplicateProductSKUError(AppException):
    """Product creation attempted with an SKU that is already registered."""

    status_code = 409

    def __init__(self, sku: str):
        super().__init__(f"A product with SKU '{sku}' already exists")


class InvalidTokenError(AppException):
    """JWT is malformed, expired, or fails signature verification."""

    status_code = 401

    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message)


class TokenRevokedError(AppException):
    """Refresh token was explicitly revoked (logout, rotation, security event)."""

    status_code = 401

    def __init__(self, message: str = "This token has been revoked"):
        super().__init__(message)


# --- Authorization ---

class PermissionDeniedError(AppException):
    """Authenticated, but lacks the specific permission required for this action."""

    status_code = 403

    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(message)


class RoleNotFoundError(AppException):
    def __init__(self, message: str = "Role not found"):
        super().__init__(message)
