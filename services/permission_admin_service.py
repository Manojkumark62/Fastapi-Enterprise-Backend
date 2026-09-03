"""
Permission admin operations — list/create permission records.

Deliberately separate from services/permission_service.py, which handles
the RBAC *check* (does user X hold permission Y). This module handles
managing the permission catalog itself. Splitting them keeps the
security-critical check function small and easy to audit in isolation.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.permission import Permission
from schemas.permission import PermissionCreateRequest


class PermissionAdminService:
    def __init__(self, db: Session):
        self.db = db

    def list_permissions(self) -> list[Permission]:
        return list(self.db.execute(select(Permission).order_by(Permission.code)).scalars().all())

    def create_permission(self, payload: PermissionCreateRequest) -> Permission:
        permission = Permission(code=payload.code, description=payload.description)
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        return permission

    def update_permission(self, permission_id: int, payload: PermissionCreateRequest) -> Permission | None:
        permission = self.db.get(Permission, permission_id)
        if permission is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(permission, field, value)
        self.db.commit()
        self.db.refresh(permission)
        return permission
