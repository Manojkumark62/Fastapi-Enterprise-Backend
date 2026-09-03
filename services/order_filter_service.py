"""Advanced order filtering and search service."""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from models.order import Order
from models.customer import Customer
from utils.query_filters import exclude_deleted
from core.constants import OrderStatusEnum
from dependencies.tenant import get_required_tenant_id
from services.search_service import SearchService


class OrderFilterService:
    """Advanced order filtering, sorting, and search (Modules 38-40)."""

    @staticmethod
    def list_orders_advanced(
        db: Session,
        customer_id: int | None = None,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Order], int]:
        """
        List orders with advanced filtering, sorting, and search.
        
        Args:
            db: Database session
            customer_id: Filter by customer
            status: Filter by status enum
            search: Search in order_number
            sort_by: Field to sort by (created_at, total_amount, status)
            sort_desc: Sort descending
            skip: Offset
            limit: Limit
        
        Returns:
            Tuple of (orders, total_count)
        """
        query = exclude_deleted(db.query(Order), Order)
        query = query.filter(Order.tenant_id == get_required_tenant_id())
        
        # Apply filters
        if customer_id:
            query = query.filter(Order.customer_id == customer_id)
        
        if status:
            try:
                OrderStatusEnum(status)
                query = query.filter(Order.status == status)
            except ValueError:
                pass
        
        if search:
            query = SearchService.apply(query, Order, search, ["order_number"])
        
        # Get total count before pagination
        total = query.count()
        
        # Apply sorting
        if sort_by == "total_amount":
            sort_col = Order.total_amount
        elif sort_by == "status":
            sort_col = Order.status
        else:
            sort_col = Order.created_at
        
        if sort_desc:
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())
        
        # Apply pagination
        orders = query.offset(skip).limit(limit).all()
        
        return orders, total

    @staticmethod
    def filter_by_date_range(
        db: Session,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[Order]:
        """Filter orders by date range."""
        query = exclude_deleted(db.query(Order), Order)
        query = query.filter(Order.tenant_id == get_required_tenant_id())
        if start_date:
            query = query.filter(Order.created_at >= start_date)
        if end_date:
            query = query.filter(Order.created_at <= end_date)
        return query.all()

    @staticmethod
    def filter_by_amount_range(
        db: Session,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
    ) -> list[Order]:
        """Filter orders by total amount range."""
        query = exclude_deleted(db.query(Order), Order)
        query = query.filter(Order.tenant_id == get_required_tenant_id())
        if min_amount is not None:
            query = query.filter(Order.total_amount >= min_amount)
        if max_amount is not None:
            query = query.filter(Order.total_amount <= max_amount)
        return query.all()
