from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductCreateRequest(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(..., gt=0, decimal_places=2)
    stock_quantity: int = Field(..., ge=0)
    category: str | None = Field(default=None, max_length=100)


class ProductUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    stock_quantity: int | None = Field(default=None, ge=0)
    category: str | None = Field(default=None, max_length=100)


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sku: str
    name: str
    description: str | None
    price: Decimal
    stock_quantity: int
    category: str | None


class ProductBulkUpdateRequest(ProductUpdateRequest):
    id: int = Field(..., gt=0)
