"""
Authentication dependencies — resolve the current user from a bearer token.

`get_current_user` is the single source of truth for "who is making this
request". Every other auth/permission dependency builds on top of it
rather than re-parsing the token independently.
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from core.security import decode_token
from core.config import settings
from dependencies.db import get_db
from dependencies.tenant import resolve_tenant_for_user
from models.user import User
from models.session import UserSession
from services.audit_service import set_audit_actor
from sqlalchemy import select
from datetime import datetime, timezone

# tokenUrl is the OAuth2 form endpoint used by the OpenAPI "Authorize" button.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
    except JWTError:
        raise credentials_exception

    if payload.get("type") != "access":
        raise credentials_exception

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except (TypeError, ValueError):
        raise credentials_exception

    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception

    if user.is_deleted:
        raise credentials_exception
    set_audit_actor(user.id)

    session_id = payload.get("sid")
    if not isinstance(session_id, str):
        raise credentials_exception
    session = db.scalar(select(UserSession).where(UserSession.session_token == session_id))
    if session is None or session.user_id != user.id or not session.is_active:
        raise credentials_exception
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        raise credentials_exception
    session.last_active_at = datetime.now(timezone.utc)
    db.commit()

    return user


def get_current_active_user(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """
    Same as get_current_user but additionally rejects deactivated accounts.
    Kept separate from get_current_user because some endpoints (e.g. an
    "account reactivation" flow) legitimately need to identify an inactive
    user without immediately rejecting the request.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated",
        )
    resolve_tenant_for_user(request, current_user, db)
    return current_user


def get_current_superuser(current_user: User = Depends(get_current_active_user)) -> User:
    """Restricts an endpoint to superusers only (escape hatch above RBAC)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires superuser privileges",
        )
    return current_user
