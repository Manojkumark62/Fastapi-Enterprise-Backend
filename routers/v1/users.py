"""User management endpoints (admin-facing)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.constants import PermissionCodeEnum
from dependencies.db import get_db
from dependencies.pagination import PaginationParams, build_paginated_response, get_pagination_params
from dependencies.permissions import require_permission, require_permission_or_self
from exceptions.custom_exceptions import RoleNotFoundError
from schemas.common import MessageResponse, PaginatedResponse
from schemas.user import UserResponse, UserUpdateRequest
from services.role_service import RoleService
from services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=PaginatedResponse[UserResponse])
def list_users(
    pagination: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.VIEW_USER)),
):
    service = UserService(db)
    users, total = service.list_users(pagination)
    return build_paginated_response(users, total, pagination)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.VIEW_USER)),
):
    service = UserService(db)
    user = service.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    _=Depends(require_permission_or_self(PermissionCodeEnum.UPDATE_USER)),
):
    service = UserService(db)
    user = service.update(user_id, payload)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def replace_user(
    user_id: int,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    _=Depends(require_permission_or_self(PermissionCodeEnum.UPDATE_USER)),
):
    service = UserService(db)
    user = service.update(user_id, payload)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete("/{user_id}", response_model=MessageResponse)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.DELETE_USER)),
):
    service = UserService(db)
    if not service.soft_delete(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return MessageResponse(message="User deleted")


@router.post("/{user_id}/roles/{role_name}", response_model=MessageResponse)
def assign_role(
    user_id: int,
    role_name: str,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.MANAGE_ROLES)),
):
    service = RoleService(db)
    try:
        service.assign_role(user_id, role_name)
    except RoleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    return MessageResponse(message=f"Role '{role_name}' assigned")


@router.delete("/{user_id}/roles/{role_name}", response_model=MessageResponse)
def revoke_role(
    user_id: int,
    role_name: str,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.MANAGE_ROLES)),
):
    service = RoleService(db)
    try:
        revoked = service.revoke_role(user_id, role_name)
    except RoleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    if not revoked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not hold this role")
    return MessageResponse(message=f"Role '{role_name}' revoked")
