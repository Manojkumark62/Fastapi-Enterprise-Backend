from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.constants import PermissionCodeEnum
from dependencies.db import get_db
from dependencies.pagination import PaginationParams, build_paginated_response, get_pagination_params
from dependencies.permissions import require_permission
from schemas.common import MessageResponse, PaginatedResponse
from schemas.employee import EmployeeCreateRequest, EmployeeResponse, EmployeeUpdateRequest
from services.employee_service import EmployeeService

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    payload: EmployeeCreateRequest,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.CREATE_USER)),
):
    return EmployeeService(db).create(payload)


@router.get("", response_model=PaginatedResponse[EmployeeResponse])
def list_employees(
    pagination: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.VIEW_USER)),
):
    items, total = EmployeeService(db).list_employees(pagination)
    return build_paginated_response(items, total, pagination)


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.VIEW_USER)),
):
    employee = EmployeeService(db).get_by_id(employee_id)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee


@router.patch("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    payload: EmployeeUpdateRequest,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.UPDATE_USER)),
):
    employee = EmployeeService(db).update(employee_id, payload)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee


@router.put("/{employee_id}", response_model=EmployeeResponse)
def replace_employee(
    employee_id: int,
    payload: EmployeeUpdateRequest,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.UPDATE_USER)),
):
    employee = EmployeeService(db).update(employee_id, payload)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee


@router.delete("/{employee_id}", response_model=MessageResponse)
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.DELETE_USER)),
):
    if not EmployeeService(db).soft_delete(employee_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return MessageResponse(message="Employee deleted")
