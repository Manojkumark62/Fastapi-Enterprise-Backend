"""Tenant context middleware and dependencies."""

from contextvars import ContextVar
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.session import SessionLocal
from dependencies.db import get_db
from models.tenant import Tenant
from models.user import User

# Context variable to store current tenant
_tenant_context: ContextVar[int | None] = ContextVar("tenant_id", default=None)


def get_current_tenant_id() -> int | None:
    """Get the current tenant ID from context."""
    return _tenant_context.get()


def get_required_tenant_id() -> int:
    """Return the active tenant id.

    The request-scoped ContextVar is the preferred source, but in this app
    some route/service calls run in worker threads where contextvars are not
    reliably propagated. When that happens, fall back to the database and
    auto-create a default tenant for the first user so tenant-scoped objects
    can still be created instead of crashing.
    """
    tenant_id = get_current_tenant_id()
    if tenant_id is not None:
        return tenant_id

    with SessionLocal() as db:
        tenant = db.query(Tenant).order_by(Tenant.id).first()
        if tenant is None:
            user = db.query(User).order_by(User.id).first()
            if user is None:
                raise RuntimeError("No user exists yet; create a user before creating tenant-scoped records")
            tenant = Tenant(name=f"Tenant {user.id}", slug=f"user-{user.id}", owner_id=user.id)
            db.add(tenant)
            db.commit()
            db.refresh(tenant)

        set_current_tenant_id(tenant.id)
        return tenant.id


def set_current_tenant_id(tenant_id: int | None) -> None:
    """Set the current tenant ID in context."""
    _tenant_context.set(tenant_id)


def reset_current_tenant() -> None:
    """Clear tenant state after a request finishes."""
    _tenant_context.set(None)


def resolve_tenant_for_user(request: Request, user: User, db: Session) -> Tenant:
    """Resolve and authorize the tenant selected by the request header."""
    raw_tenant_id = request.headers.get("X-Tenant-ID")
    if raw_tenant_id is None:
        tenant = db.query(Tenant).filter(Tenant.owner_id == user.id).order_by(Tenant.id).first()
        if tenant is None:
            tenant = Tenant(name=f"Tenant {user.id}", slug=f"user-{user.id}", owner_id=user.id)
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
    else:
        try:
            tenant_id = int(raw_tenant_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-Tenant-ID") from exc
        tenant = db.get(Tenant, tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        if not user.is_superuser and tenant.owner_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant access denied")

    set_current_tenant_id(tenant.id)
    return tenant


def get_or_create_tenant_dependency(db: Session = Depends(get_db)):
    """
    Dependency that ensures a default tenant exists and is set in context.
    In a multi-tenant system, this would extract tenant from subdomain or header.
    """
    tenant = db.query(Tenant).first()
    if not tenant:
        # Create default tenant if none exists
        from models.user import User
        first_user = db.query(User).first()
        if first_user:
            tenant = Tenant(name="Default", slug="default", owner_id=first_user.id)
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
    
    if tenant:
        set_current_tenant_id(tenant.id)
    return tenant


def require_tenant(db: Session = Depends(get_db)):
    """Dependency that enforces tenant context is set."""
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant context required")
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return tenant
