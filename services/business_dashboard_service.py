from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.constants import OrderStatusEnum, TaskStatusEnum
from dependencies.tenant import get_required_tenant_id
from models.customer import Customer
from models.notification import Notification
from models.order import Order
from models.payment import Payment
from models.product import Product
from models.task import Task
from utils.query_filters import exclude_deleted


class BusinessDashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.tenant_id = get_required_tenant_id()

    def summary(self, user_id: int) -> dict:
        def count(model, *conditions):
            statement = exclude_deleted(select(func.count()), model).where(
                model.tenant_id == self.tenant_id, *conditions
            )
            return self.db.scalar(statement) or 0

        revenue = self.db.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).join(
            Order, Order.id == Payment.order_id
        ).where(
            Payment.tenant_id == self.tenant_id,
            Payment.status == "success",
            Order.tenant_id == self.tenant_id,
        )) or Decimal("0")
        pending_tasks = count(Task, Task.status == TaskStatusEnum.TODO.value)
        return {
            "customers": count(Customer),
            "products": count(Product),
            "orders": count(Order),
            "pending_orders": count(Order, Order.status == OrderStatusEnum.PENDING.value),
            "revenue": revenue,
            "low_stock_products": count(Product, Product.stock_quantity <= 5),
            "pending_tasks": pending_tasks,
            "unread_notifications": self.db.scalar(select(func.count()).select_from(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )) or 0,
        }