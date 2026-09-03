"""
Permission service — the actual RBAC check: does this user hold a given
permission, by way of any role assigned to them?

This is intentionally a single, well-tested query rather than something
duplicated across dependencies/permissions.py and route handlers. Every
permission check in the app goes through `user_has_permission`.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.constants import PermissionCodeEnum, UserRoleEnum
from models.permission import Permission
from models.role import Role
from models.role_permission import RolePermission
from models.user_role import UserRole


class PermissionService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_permission_codes(self, user_id: int) -> set[str]:
        """
        Returns the full set of permission codes a user holds across all
        of their assigned roles. A set (not a list) because a user can
        hold the same permission via more than one role, and callers only
        ever care about membership, not counts.

        Admin-role users inherit every permission automatically, even if
        their role-to-permission mappings are incomplete or they are not
        flagged as a superuser in the user record.
        """
        rows = self.db.execute(
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(UserRole.user_id == user_id)
        ).scalars().all()

        permission_codes = set(rows)
        is_admin = self.db.execute(
            select(UserRole.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id, Role.name == UserRoleEnum.ADMIN.value)
        ).first() is not None

        if is_admin:
            permission_codes.update(code.value for code in PermissionCodeEnum)

        return permission_codes

    def user_has_permission(self, user_id: int, permission_code: str) -> bool:
        return permission_code in self.get_user_permission_codes(user_id)

    def user_has_any_permission(self, user_id: int, permission_codes: list[str]) -> bool:
        held = self.get_user_permission_codes(user_id)
        return any(code in held for code in permission_codes)

    def user_has_all_permissions(self, user_id: int, permission_codes: list[str]) -> bool:
        held = self.get_user_permission_codes(user_id)
        return all(code in held for code in permission_codes)
