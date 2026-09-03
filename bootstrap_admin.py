"""One-time bootstrap script for the first admin user.

Run once after database setup:
    python bootstrap_admin.py
"""

from sqlalchemy import select

from core.constants import PermissionCodeEnum
from core.security import hash_password
from database.session import SessionLocal
from models.permission import Permission
from models.role import Role
from models.role_permission import RolePermission
from models.user import User
from models.user_role import UserRole


def ensure_permission(db, code: str) -> Permission:
    permission = db.execute(select(Permission).where(Permission.code == code)).scalar_one_or_none()
    if permission is None:
        permission = Permission(code=code, description=f"Permission: {code}")
        db.add(permission)
        db.commit()
        db.refresh(permission)
    return permission


def ensure_role(db, name: str) -> Role:
    role = db.execute(select(Role).where(Role.name == name)).scalar_one_or_none()
    if role is None:
        role = Role(name=name, description=f"{name} role")
        db.add(role)
        db.commit()
        db.refresh(role)
    return role


def ensure_role_permission(db, role: Role, permission: Permission) -> None:
    exists = db.execute(
        select(RolePermission).where(
            RolePermission.role_id == role.id,
            RolePermission.permission_id == permission.id,
        )
    ).scalar_one_or_none()
    if exists is None:
        db.add(RolePermission(role_id=role.id, permission_id=permission.id))
        db.commit()


def ensure_user_role(db, user_id: int, role_id: int) -> None:
    exists = db.execute(
        select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
    ).scalar_one_or_none()
    if exists is None:
        db.add(UserRole(user_id=user_id, role_id=role_id))
        db.commit()


def bootstrap_admin(email: str, password: str, full_name: str) -> None:
    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if user is None:
            user = User(
                email=email,
                hashed_password=hash_password(password),
                full_name=full_name,
                is_active=True,
                is_verified=True,
                is_superuser=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            user.is_superuser = True
            user.is_active = True
            user.is_verified = True
            db.commit()

        admin_role = ensure_role(db, "ADMIN")
        for permission in PermissionCodeEnum:
            ensure_role_permission(db, admin_role, ensure_permission(db, permission.value))

        ensure_user_role(db, user.id, admin_role.id)
        print(f"Admin bootstrapped: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    bootstrap_admin(
    email="manojkumarkancharla143@gmail.com",
    password="StrongPassword123!",
    full_name="System Admin",
)
