from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.constants import PermissionCodeEnum
from dependencies.db import get_db
from dependencies.pagination import PaginationParams, build_paginated_response, get_pagination_params
from dependencies.permissions import require_permission
from schemas.common import MessageResponse, PaginatedResponse
from schemas.customer import CustomerCreateRequest, CustomerResponse, CustomerUpdateRequest
from services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerCreateRequest,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.CREATE_USER)),
):
    return CustomerService(db).create(payload)


@router.get("", response_model=PaginatedResponse[CustomerResponse])
def list_customers(
    pagination: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.VIEW_USER)),
):
    items, total = CustomerService(db).list_customers(pagination)
    return build_paginated_response(items, total, pagination)


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.VIEW_USER)),
):
    customer = CustomerService(db).get_by_id(customer_id)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


@router.patch("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    payload: CustomerUpdateRequest,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.UPDATE_USER)),
):
    customer = CustomerService(db).update(customer_id, payload)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
def replace_customer(
    customer_id: int,
    payload: CustomerUpdateRequest,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.UPDATE_USER)),
):
    customer = CustomerService(db).update(customer_id, payload)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


@router.delete("/{customer_id}", response_model=MessageResponse)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.DELETE_USER)),
):
    if not CustomerService(db).soft_delete(customer_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return MessageResponse(message="Customer deleted")
