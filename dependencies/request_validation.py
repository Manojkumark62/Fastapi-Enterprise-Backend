"""Reusable validation dependencies for common resource query parameters."""

from dataclasses import dataclass
from decimal import Decimal

from fastapi import HTTPException, Query, status


@dataclass
class ProductFilters:
    category: str | None
    categories: list[str] | None
    name: str | None
    min_price: Decimal | None
    max_price: Decimal | None
    sort_by: str
    sort_order: str


def get_product_filters(
    category: str | None = Query(default=None, min_length=1, max_length=100),
    categories: list[str] | None = Query(default=None, min_length=1),
    name: str | None = Query(default=None, min_length=1, max_length=255),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    sort_by: str = Query(default="id"),
    sort_order: str = Query(default="asc", pattern="^(asc|desc)$"),
) -> ProductFilters:
    if sort_by not in {"id", "name", "price", "category", "stock_quantity"}:
        raise HTTPException(status_code=422, detail="Unsupported product sort field")
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="min_price must be less than or equal to max_price",
        )
    return ProductFilters(
        category=category,
        categories=categories,
        name=name,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        sort_order=sort_order,
    )