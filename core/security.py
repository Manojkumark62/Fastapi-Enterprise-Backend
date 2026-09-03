"""
Core security primitives: password hashing and JWT issuance/verification.

This module is intentionally the ONLY place that touches passlib or
python-jose directly. Every service that needs to hash a password or
issue/verify a token imports from here, so hashing algorithm and token
format stay consistent across the whole app.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import uuid4

from jose import JWTError, jwt
import bcrypt

from core.config import settings

# --------------------------------------------------------------------------
# Password hashing
# --------------------------------------------------------------------------

def hash_password(plain_password: str) -> str:
    """Hash a plaintext password for storage."""
    if len(plain_password.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 UTF-8 bytes")
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# --------------------------------------------------------------------------
# JWT tokens
# --------------------------------------------------------------------------

TokenType = Literal["access", "refresh"]


def _create_token(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    to_encode: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid4()),  # unique token id, useful for refresh-token revocation
    }
    if extra_claims:
        reserved = {"sub", "type", "iat", "exp", "jti"}
        if reserved.intersection(extra_claims):
            raise ValueError("extra_claims cannot override reserved JWT claims")
        to_encode.update(extra_claims)

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    """
    Create a short-lived access token.
    `subject` is typically the user's id (as a string).
    """
    return _create_token(
        subject=subject,
        token_type="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims=extra_claims,
    )


def create_refresh_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    """Create a long-lived refresh token."""
    return _create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        extra_claims=extra_claims,
    )


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT. Raises jose.JWTError (or subclasses like
    ExpiredSignatureError) if the token is invalid or expired — callers
    are expected to catch these and translate to an HTTP 401.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def decode_token_safe(token: str) -> dict[str, Any] | None:
    """Same as decode_token but returns None instead of raising."""
    try:
        return decode_token(token)
    except JWTError:
        return None
