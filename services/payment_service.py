from sqlalchemy import select
from sqlalchemy.orm import Session

from core.constants import PaymentStatusEnum
from models.order import Order
from models.payment import Payment
from schemas.payment import PaymentCreateRequest
from dependencies.tenant import get_required_tenant_id


class OrderNotFoundError(Exception):
    pass


class PaymentAmountMismatchError(Exception):
    def __init__(self, expected, actual):
        self.expected = expected
        self.actual = actual
        super().__init__(f"Payment amount {actual} does not match order total {expected}")


class PaymentService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: PaymentCreateRequest) -> Payment:
        tenant_id = get_required_tenant_id()
        existing = self.db.scalar(
            select(Payment).where(
                Payment.idempotency_key == payload.idempotency_key,
                Payment.tenant_id == tenant_id,
            )
        )
        if existing is not None:
            if existing.order_id != payload.order_id or existing.amount != payload.amount:
                raise ValueError("Idempotency key was already used with a different payment")
            return existing
        order = self.db.execute(
            select(Order).where(
                Order.id == payload.order_id,
                Order.tenant_id == tenant_id,
            ).with_for_update()
        ).scalar_one_or_none()
        if order is None or order.is_deleted:
            raise OrderNotFoundError(f"Order {payload.order_id} not found")

        # Guard against a payment for the wrong amount ever being recorded
        # as if it settled the order — this is a correctness check, not
        # just a nicety, since total_amount downstream reporting relies on
        # payments actually matching what was ordered.
        if payload.amount != order.total_amount:
            raise PaymentAmountMismatchError(order.total_amount, payload.amount)

        existing = self.db.scalar(
            select(Payment).where(
                Payment.order_id == payload.order_id,
                Payment.tenant_id == tenant_id,
                Payment.status == PaymentStatusEnum.SUCCESS.value,
            )
        )
        if existing is not None:
            raise ValueError("Order already has a successful payment")

        payment = Payment(
            order_id=payload.order_id,
            tenant_id=tenant_id,
            amount=payload.amount,
            status=PaymentStatusEnum.SUCCESS.value,
            payment_method=payload.payment_method,
            transaction_reference=payload.transaction_reference,
            idempotency_key=payload.idempotency_key,
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def get_by_id(self, payment_id: int) -> Payment | None:
        return self.db.scalar(
            select(Payment).where(
                Payment.id == payment_id,
                Payment.tenant_id == get_required_tenant_id(),
            )
        )

    def list_for_order(self, order_id: int) -> list[Payment]:
        return list(self.db.execute(
            select(Payment).where(
                Payment.order_id == order_id,
                Payment.tenant_id == get_required_tenant_id(),
            )
        ).scalars().all())

    def refund(self, payment_id: int, amount=None) -> Payment | None:
        payment = self.db.execute(
            select(Payment).where(
                Payment.id == payment_id,
                Payment.tenant_id == get_required_tenant_id(),
            ).with_for_update()
        ).scalar_one_or_none()
        if payment is None or payment.status not in (PaymentStatusEnum.SUCCESS.value, PaymentStatusEnum.REFUNDED.value):
            return None
        refund_amount = amount or payment.amount
        if refund_amount <= 0 or payment.refunded_amount + refund_amount > payment.amount:
            return None
        payment.refunded_amount += refund_amount
        if payment.refunded_amount == payment.amount:
            payment.status = PaymentStatusEnum.REFUNDED.value
        self.db.commit()
        self.db.refresh(payment)
        return payment
