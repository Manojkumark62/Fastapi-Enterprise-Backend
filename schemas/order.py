from datetime import datetime
from decimal import Decimal

from core.constants import OrderStatusEnum
from pydantic import BaseModel, ConfigDict, Field


class OrderItemCreateRequest(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class OrderCreateRequest(BaseModel):
    customer_id: int = Field(..., gt=0)
    items: list[OrderItemCreateRequest] = Field(..., min_length=1)
    shipping_address: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=500)


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_number: str
    customer_id: int
    status: str
    total_amount: Decimal
    shipping_address: str | None
    notes: str | None
    items: list[OrderItemResponse]
    created_at: datetime


class OrderStatusUpdateRequest(BaseModel):
    status: OrderStatusEnum
