from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.constants import PermissionCodeEnum
from dependencies.db import get_db
from dependencies.permissions import require_permission
from schemas.role import RoleCreateRequest, RoleResponse
from services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("", response_model=list[RoleResponse])
def list_roles(
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.MANAGE_ROLES)),
):
    return RoleService(db).list_roles()


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    payload: RoleCreateRequest,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.MANAGE_ROLES)),
):
    return RoleService(db).create_role(payload)


@router.put("/{role_id}", response_model=RoleResponse)
def replace_role(
    role_id: int,
    payload: RoleCreateRequest,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.MANAGE_ROLES)),
):
    role = RoleService(db).update_role(role_id, payload)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role
