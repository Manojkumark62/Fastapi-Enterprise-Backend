from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreateRequest(BaseModel):
    order_id: int
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    payment_method: str | None = Field(default=None, max_length=50)
    transaction_reference: str | None = Field(default=None, max_length=255)
    idempotency_key: str = Field(..., min_length=8, max_length=255)


class PaymentRefundRequest(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, decimal_places=2)


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_id: int
    amount: Decimal
    status: str
    payment_method: str | None
    transaction_reference: str | None
    refunded_amount: Decimal
    created_at: datetime
