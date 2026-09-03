from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.constants import PermissionCodeEnum
from dependencies.db import get_db
from dependencies.permissions import require_permission
from schemas.payment import PaymentCreateRequest, PaymentRefundRequest, PaymentResponse
from services.payment_service import OrderNotFoundError, PaymentAmountMismatchError, PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreateRequest,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.UPDATE_ORDER)),
):
    service = PaymentService(db)
    try:
        return service.create(payload)
    except OrderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PaymentAmountMismatchError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.VIEW_ORDER)),
):
    payment = PaymentService(db).get_by_id(payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment


@router.post("/{payment_id}/refund", response_model=PaymentResponse)
def refund_payment(
    payment_id: int,
    payload: PaymentRefundRequest = PaymentRefundRequest(),
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.UPDATE_ORDER)),
):
    payment = PaymentService(db).refund(payment_id, payload.amount)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment cannot be refunded")
    return payment


@router.get("/order/{order_id}", response_model=list[PaymentResponse])
def list_payments_for_order(
    order_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.VIEW_ORDER)),
):
    return PaymentService(db).list_for_order(order_id)
