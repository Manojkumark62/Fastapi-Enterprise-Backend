"""
Order service — the most transactionally sensitive service in this pass.

Design decisions:
- Total is ALWAYS computed server-side from each product's current price
  at the moment of order creation, never accepted from the client. A
  client-supplied total is a direct path to price manipulation.
- Stock is reserved via ProductService.reserve_stock() for every line
  item BEFORE the order is committed, inside the same db.commit(). If
  any line item has insufficient stock, the whole transaction rolls
  back — no partial order with some items reserved and others not.
  reserve_stock()/release_stock() deliberately don't call commit()
  themselves for exactly this reason: this method owns the transaction
  boundary, not the product service.
- order_number is generated here rather than left to the DB, so it's
  available immediately on the in-memory object before the row exists.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from core.constants import OrderStatusEnum
from dependencies.pagination import PaginationParams
from dependencies.tenant import get_required_tenant_id
from models.customer import Customer
from models.order import Order
from models.order_item import OrderItem
from schemas.order import OrderCreateRequest
from services.product_service import InsufficientStockError, ProductService
from utils.query_filters import exclude_deleted


class CustomerNotFoundError(Exception):
    pass


class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.product_service = ProductService(db)

    def _generate_order_number(self) -> str:
        return f"ORD-{uuid.uuid4().hex[:10].upper()}"

    def create(self, payload: OrderCreateRequest) -> Order:
        tenant_id = get_required_tenant_id()
        customer = self.db.scalar(
            select(Customer).where(
                Customer.id == payload.customer_id,
                Customer.tenant_id == tenant_id,
            )
        )
        if customer is None or customer.is_deleted:
            raise CustomerNotFoundError(f"Customer {payload.customer_id} not found")

        order = Order(
            order_number=self._generate_order_number(),
            tenant_id=tenant_id,
            customer_id=payload.customer_id,
            status=OrderStatusEnum.PENDING.value,
            total_amount=0,  # computed below, before commit
            shipping_address=payload.shipping_address,
            notes=payload.notes,
        )
        self.db.add(order)
        self.db.flush()  # assigns order.id without committing, so OrderItem FKs can reference it

        total = 0
        for item_req in payload.items:
            product = self.product_service.get_by_id(item_req.product_id)
            if product is None:
                # Rollback everything reserved so far in this loop — the
                # whole request is one transaction, not item-by-item.
                self.db.rollback()
                raise InsufficientStockError(item_req.product_id, item_req.quantity, 0)

            # Reserve stock — raises InsufficientStockError if unavailable.
            # Does NOT commit; if this raises, the caller's except block
            # (see routers/v1/orders.py) rolls back the whole session,
            # undoing any stock already decremented earlier in this loop.
            self.product_service.reserve_stock(product.id, item_req.quantity)

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item_req.quantity,
                unit_price=product.price,  # snapshot at time of purchase
            )
            self.db.add(order_item)
            total += product.price * item_req.quantity

        order.total_amount = total
        self.db.commit()
        self.db.refresh(order)
        return self.get_by_id(order.id)  # re-fetch with items eagerly loaded

    def get_by_id(self, order_id: int) -> Order | None:
        order = self.db.execute(
            select(Order).options(selectinload(Order.items)).where(
                Order.id == order_id,
                Order.tenant_id == get_required_tenant_id(),
            )
        ).scalar_one_or_none()
        if order is not None and order.is_deleted:
            return None
        return order

    def list_orders(
        self, pagination: PaginationParams, customer_id: int | None = None, status_filter: str | None = None
    ) -> tuple[list[Order], int]:
        base = exclude_deleted(select(Order), Order)
        base = base.where(Order.tenant_id == get_required_tenant_id())
        if customer_id is not None:
            base = base.where(Order.customer_id == customer_id)
        if status_filter is not None:
            base = base.where(Order.status == status_filter)

        total = self.db.execute(select(func.count()).select_from(base.subquery())).scalar_one()
        rows = self.db.execute(
            base.options(selectinload(Order.items))
            .order_by(Order.id.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        ).scalars().all()
        return list(rows), total

    def update_status(self, order_id: int, new_status: str) -> Order | None:
        order = self.get_by_id(order_id)
        if order is None:
            return None

        # Cancelling a still-pending/confirmed order releases its reserved
        # stock back to inventory. Already-shipped orders don't release
        # stock on cancellation — that's a return/refund flow, not this one.
        if (
            new_status == OrderStatusEnum.CANCELLED.value
            and order.status in (OrderStatusEnum.PENDING.value, OrderStatusEnum.CONFIRMED.value)
        ):
            for item in order.items:
                self.product_service.release_stock(item.product_id, item.quantity)

        order.status = new_status
        self.db.commit()
        self.db.refresh(order)
        return order
