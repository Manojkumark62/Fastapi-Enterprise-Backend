from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.constants import PermissionCodeEnum
from dependencies.db import get_db
from dependencies.pagination import PaginationParams, build_paginated_response, get_pagination_params
from dependencies.permissions import require_permission
from schemas.common import PaginatedResponse
from schemas.order import OrderCreateRequest, OrderResponse, OrderStatusUpdateRequest
from services.order_service import CustomerNotFoundError, OrderService
from services.product_service import InsufficientStockError

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreateRequest,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.CREATE_ORDER)),
):
    service = OrderService(db)
    try:
        return service.create(payload)
    except CustomerNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InsufficientStockError as e:
        # 409 Conflict: the request is well-formed but can't be satisfied
        # against current stock state — distinct from a 400 (bad input)
        # or 404 (missing resource).
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("", response_model=PaginatedResponse[OrderResponse])
def list_orders(
    customer_id: int | None = None,
    status_filter: str | None = None,
    pagination: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.VIEW_ORDER)),
):
    items, total = OrderService(db).list_orders(pagination, customer_id=customer_id, status_filter=status_filter)
    return build_paginated_response(items, total, pagination)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.VIEW_ORDER)),
):
    order = OrderService(db).get_by_id(order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdateRequest,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.UPDATE_ORDER)),
):
    order = OrderService(db).update_status(order_id, payload.status)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order
