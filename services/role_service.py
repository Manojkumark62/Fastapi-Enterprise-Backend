"""Role service — assigning/revoking roles, role-level checks, admin CRUD."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.constants import PermissionCodeEnum, UserRoleEnum
from exceptions.custom_exceptions import RoleNotFoundError
from models.permission import Permission
from models.role import Role
from models.role_permission import RolePermission
from models.user_role import UserRole
from schemas.role import RoleCreateRequest


class RoleService:
    def __init__(self, db: Session):
        self.db = db

    def ensure_default_roles_and_permissions(self) -> None:
        """Create the default RBAC catalog if it does not already exist."""
        role_names = {UserRoleEnum.ADMIN.value, UserRoleEnum.MANAGER.value, UserRoleEnum.USER.value}
        for role_name in role_names:
            if self.get_role_by_name(role_name) is None:
                self.db.add(Role(name=role_name, description=f"{role_name} role"))
        self.db.commit()

        for permission_code in PermissionCodeEnum:
            permission = self.db.execute(
                select(Permission).where(Permission.code == permission_code.value)
            ).scalar_one_or_none()
            if permission is None:
                self.db.add(Permission(code=permission_code.value, description=permission_code.value))
        self.db.commit()

        admin_role = self.get_role_by_name(UserRoleEnum.ADMIN.value)
        manager_role = self.get_role_by_name(UserRoleEnum.MANAGER.value)
        user_role = self.get_role_by_name(UserRoleEnum.USER.value)

        if admin_role is not None:
            for permission_code in PermissionCodeEnum:
                permission = self.db.execute(
                    select(Permission).where(Permission.code == permission_code.value)
                ).scalar_one_or_none()
                if permission is not None:
                    exists = self.db.execute(
                        select(RolePermission).where(
                            RolePermission.role_id == admin_role.id,
                            RolePermission.permission_id == permission.id,
                        )
                    ).scalar_one_or_none()
                    if exists is None:
                        self.db.add(RolePermission(role_id=admin_role.id, permission_id=permission.id))

        if manager_role is not None:
            basic_permissions = {
                PermissionCodeEnum.VIEW_USER,
                PermissionCodeEnum.VIEW_ORDER,
                PermissionCodeEnum.VIEW_REPORT,
            }
            for permission_code in basic_permissions:
                permission = self.db.execute(
                    select(Permission).where(Permission.code == permission_code.value)
                ).scalar_one_or_none()
                if permission is not None:
                    exists = self.db.execute(
                        select(RolePermission).where(
                            RolePermission.role_id == manager_role.id,
                            RolePermission.permission_id == permission.id,
                        )
                    ).scalar_one_or_none()
                    if exists is None:
                        self.db.add(RolePermission(role_id=manager_role.id, permission_id=permission.id))

        if user_role is not None:
            default_user_permissions = {
                PermissionCodeEnum.VIEW_USER,
                PermissionCodeEnum.VIEW_ORDER,
            }
            for permission_code in default_user_permissions:
                permission = self.db.execute(
                    select(Permission).where(Permission.code == permission_code.value)
                ).scalar_one_or_none()
                if permission is not None:
                    exists = self.db.execute(
                        select(RolePermission).where(
                            RolePermission.role_id == user_role.id,
                            RolePermission.permission_id == permission.id,
                        )
                    ).scalar_one_or_none()
                    if exists is None:
                        self.db.add(RolePermission(role_id=user_role.id, permission_id=permission.id))

        self.db.commit()

    def list_roles(self) -> list[Role]:
        return list(self.db.execute(select(Role).order_by(Role.name)).scalars().all())

    def create_role(self, payload: RoleCreateRequest) -> Role:
        role = Role(name=payload.name, description=payload.description)
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def update_role(self, role_id: int, payload: RoleCreateRequest) -> Role | None:
        role = self.db.get(Role, role_id)
        if role is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(role, field, value)
        self.db.commit()
        self.db.refresh(role)
        return role

    def get_role_by_name(self, name: str) -> Role | None:
        return self.db.execute(select(Role).where(Role.name == name)).scalar_one_or_none()

    def assign_default_user_role(self, user_id: int) -> UserRole:
        self.ensure_default_roles_and_permissions()
        user_role = self.get_role_by_name(UserRoleEnum.USER.value)
        if user_role is None:
            raise RoleNotFoundError("Default USER role does not exist")
        return self.assign_role(user_id, UserRoleEnum.USER.value)

    def get_user_role_names(self, user_id: int) -> set[str]:
        rows = self.db.execute(
            select(Role.name).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user_id)
        ).scalars().all()
        return set(rows)

    def user_has_role(self, user_id: int, role_name: str) -> bool:
        return role_name in self.get_user_role_names(user_id)

    def assign_role(self, user_id: int, role_name: str) -> UserRole:
        role = self.get_role_by_name(role_name)
        if role is None:
            raise RoleNotFoundError(f"Role '{role_name}' does not exist")

        existing = self.db.execute(
            select(UserRole)
            .where(UserRole.user_id == user_id)
            .where(UserRole.role_id == role.id)
        ).scalar_one_or_none()

        if existing is not None:
            return existing  # idempotent — assigning an already-held role is a no-op, not an error

        user_role = UserRole(user_id=user_id, role_id=role.id)
        self.db.add(user_role)
        self.db.commit()
        self.db.refresh(user_role)
        return user_role

    def revoke_role(self, user_id: int, role_name: str) -> bool:
        """Returns True if a role was actually revoked, False if the user didn't have it."""
        role = self.get_role_by_name(role_name)
        if role is None:
            raise RoleNotFoundError(f"Role '{role_name}' does not exist")

        user_role = self.db.execute(
            select(UserRole)
            .where(UserRole.user_id == user_id)
            .where(UserRole.role_id == role.id)
        ).scalar_one_or_none()

        if user_role is None:
            return False

        self.db.delete(user_role)
        self.db.commit()
        return True
