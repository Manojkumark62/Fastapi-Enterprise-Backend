"""
Permission-checking dependencies.

`require_permission(...)` is a dependency FACTORY, not a dependency
itself — it returns a callable FastAPI can use with Depends(). This is
what lets a route declare its exact permission requirement inline:

    @router.delete("/users/{user_id}")
    def delete_user(
        user_id: int,
        current_user: User = Depends(require_permission(PermissionCodeEnum.DELETE_USER)),
    ):
        ...

This composes with get_current_user (auth) rather than duplicating token
parsing — it resolves the current user first, then layers a permission
check on top, so "who are you" and "what can you do" stay separate
concerns that combine cleanly.
"""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from core.constants import PermissionCodeEnum
from dependencies.auth import get_current_active_user
from dependencies.db import get_db
from dependencies.tenant import resolve_tenant_for_user
from models.user import User
from services.permission_service import PermissionService


def require_role(*roles: str):
    """Require one of the named application roles after authentication."""
    allowed_roles = {role.value if hasattr(role, "value") else role for role in roles}

    def dependency(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.is_superuser:
            return current_user
        user_roles = {assignment.role.name for assignment in current_user.user_roles}
        if not user_roles.intersection(allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Required role not assigned",
            )
        return current_user

    return dependency


def require_permission(permission_code: PermissionCodeEnum | str):
    """
    Returns a dependency that resolves the current user and verifies they
    hold `permission_code`. Superusers bypass the check entirely — they
    are the escape hatch above RBAC, consistent with
    dependencies/auth.py's get_current_superuser.
    """
    code_value = permission_code.value if isinstance(permission_code, PermissionCodeEnum) else permission_code

    def dependency(
        request: Request,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ) -> User:
        resolve_tenant_for_user(request, current_user, db)
        if current_user.is_superuser:
            return current_user

        permission_service = PermissionService(db)
        if not permission_service.user_has_permission(current_user.id, code_value):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {code_value}",
            )
        return current_user

    return dependency


def require_permission_or_self(permission_code: PermissionCodeEnum | str):
    """Allow a user to act on their own record without admin-only permission."""
    code_value = permission_code.value if isinstance(permission_code, PermissionCodeEnum) else permission_code

    def dependency(
        request: Request,
        user_id: int,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ) -> User:
        resolve_tenant_for_user(request, current_user, db)
        if current_user.is_superuser or current_user.id == user_id:
            return current_user

        permission_service = PermissionService(db)
        if not permission_service.user_has_permission(current_user.id, code_value):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {code_value}",
            )
        return current_user

    return dependency


def require_any_permission(*permission_codes: PermissionCodeEnum | str):
    """Like require_permission, but passes if the user holds ANY of the given codes."""
    code_values = [
        code.value if isinstance(code, PermissionCodeEnum) else code for code in permission_codes
    ]

    def dependency(
        request: Request,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ) -> User:
        resolve_tenant_for_user(request, current_user, db)
        if current_user.is_superuser:
            return current_user

        permission_service = PermissionService(db)
        if not permission_service.user_has_any_permission(current_user.id, code_values):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission (any of): {', '.join(code_values)}",
            )
        return current_user

    return dependency
