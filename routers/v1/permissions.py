from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.constants import PermissionCodeEnum
from dependencies.db import get_db
from dependencies.permissions import require_permission
from schemas.permission import PermissionCreateRequest, PermissionResponse
from services.permission_admin_service import PermissionAdminService

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get("", response_model=list[PermissionResponse])
def list_permissions(
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.MANAGE_ROLES)),
):
    return PermissionAdminService(db).list_permissions()


@router.post("", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
def create_permission(
    payload: PermissionCreateRequest,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.MANAGE_ROLES)),
):
    return PermissionAdminService(db).create_permission(payload)


@router.put("/{permission_id}", response_model=PermissionResponse)
def replace_permission(
    permission_id: int,
    payload: PermissionCreateRequest,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.MANAGE_ROLES)),
):
    permission = PermissionAdminService(db).update_permission(permission_id, payload)
    if permission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    return permission
