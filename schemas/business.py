from decimal import Decimal

from pydantic import BaseModel


class BusinessDashboardResponse(BaseModel):
    customers: int
    products: int
    orders: int
    pending_orders: int
    revenue: Decimal
    low_stock_products: int
    pending_tasks: int
    unread_notifications: int