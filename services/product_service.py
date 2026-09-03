from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from dependencies.pagination import PaginationParams
from dependencies.request_validation import ProductFilters
from services.enterprise_service import add_audit_log, add_history
from dependencies.tenant import get_required_tenant_id
from models.product import Product
from schemas.product import ProductBulkUpdateRequest, ProductCreateRequest, ProductUpdateRequest
from utils.query_filters import exclude_deleted
from utils.query_filters import apply_sort
from core.cache import cache_delete, cache_delete_prefix, tenant_cache_key
from exceptions.custom_exceptions import DuplicateProductSKUError


class InsufficientStockError(Exception):
    def __init__(self, product_id: int, requested: int, available: int):
        self.product_id = product_id
        self.requested = requested
        self.available = available
        super().__init__(
            f"Product {product_id}: requested {requested}, only {available} in stock"
        )


class ProductService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: ProductCreateRequest) -> Product:
        if self.db.scalar(select(Product.id).where(Product.sku == payload.sku)) is not None:
            raise DuplicateProductSKUError(payload.sku)

        product = Product(**payload.model_dump(), tenant_id=get_required_tenant_id())
        self.db.add(product)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            if "ix_products_sku" in str(exc.orig):
                raise DuplicateProductSKUError(payload.sku) from exc
            raise
        self.db.refresh(product)
        return product

    def get_by_id(self, product_id: int) -> Product | None:
        product = self.db.scalar(
            select(Product).where(Product.id == product_id, Product.tenant_id == get_required_tenant_id())
        )
        if product is not None and product.is_deleted:
            return None
        return product

    def list_products(
        self, pagination: PaginationParams, filters: ProductFilters | None = None,
        category: str | None = None,
    ) -> tuple[list[Product], int]:
        base = exclude_deleted(select(Product), Product)
        base = base.where(Product.tenant_id == get_required_tenant_id())
        if category is not None:
            base = base.where(Product.category == category)
        if filters is not None:
            if filters.category is not None:
                base = base.where(Product.category == filters.category)
            if filters.categories:
                base = base.where(Product.category.in_(filters.categories))
            if filters.name is not None:
                base = base.where(Product.name.ilike(f"%{filters.name}%"))
            if filters.min_price is not None:
                base = base.where(Product.price >= filters.min_price)
            if filters.max_price is not None:
                base = base.where(Product.price <= filters.max_price)

        total = self.db.execute(select(func.count()).select_from(base.subquery())).scalar_one()
        if filters is not None:
            base = apply_sort(base, Product, filters.sort_by, filters.sort_order)
        else:
            base = base.order_by(Product.id.asc())
        rows = self.db.execute(
            base.offset(pagination.offset).limit(pagination.limit)
        ).scalars().all()
        return list(rows), total

    def update(self, product_id: int, payload: ProductUpdateRequest) -> Product | None:
        product = self.db.scalar(
            select(Product)
            .where(Product.id == product_id, Product.tenant_id == get_required_tenant_id(), Product.is_deleted.is_(False))
            .with_for_update()
        )
        if product is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
        self.db.commit()
        self.db.refresh(product)
        return product

    def replace(self, product_id: int, payload: ProductCreateRequest) -> Product | None:
        product = self.get_by_id(product_id)
        if product is None:
            return None
        for field, value in payload.model_dump().items():
            setattr(product, field, value)
        self.db.commit()
        self.db.refresh(product)
        return product

    def bulk_delete(self, product_ids: list[int]) -> int:
        deleted = 0
        try:
            for product_id in product_ids:
                if self.soft_delete(product_id, commit=False):
                    deleted += 1
            self.db.commit()
            return deleted
        except Exception:
            self.db.rollback()
            raise

    def bulk_create(self, payloads: list[ProductCreateRequest]) -> list[Product]:
        products = [Product(**payload.model_dump(), tenant_id=get_required_tenant_id()) for payload in payloads]
        try:
            self.db.add_all(products)
            self.db.flush()
            self.db.commit()
            for product in products:
                self.db.refresh(product)
            return products
        except Exception:
            self.db.rollback()
            raise

    def bulk_update(self, payloads: list[ProductBulkUpdateRequest]) -> list[Product]:
        try:
            products = []
            for payload in payloads:
                product = self.db.scalar(select(Product).where(
                    Product.id == payload.id,
                    Product.tenant_id == get_required_tenant_id(),
                    Product.is_deleted.is_(False),
                ).with_for_update())
                if product is None:
                    raise ValueError(f"Product {payload.id} not found")
                for field, value in payload.model_dump(exclude={"id"}, exclude_unset=True).items():
                    setattr(product, field, value)
                products.append(product)
            self.db.commit()
            return products
        except Exception:
            self.db.rollback()
            raise

    def soft_delete(self, product_id: int, *, commit: bool = True) -> bool:
        product = self.get_by_id(product_id)
        if product is None:
            return False
        product.soft_delete()
        if commit:
            self.db.commit()
        return True

    def reserve_stock(self, product_id: int, quantity: int) -> None:
        """
        Decrements stock_quantity by `quantity`, raising InsufficientStockError
        instead of allowing stock to go negative. Called by OrderService
        inside the same transaction as order creation — see order_service.py
        for why this method deliberately does NOT commit.
        """
        product = self.db.scalar(
            select(Product)
            .where(Product.id == product_id, Product.tenant_id == get_required_tenant_id(), Product.is_deleted.is_(False))
            .with_for_update()
        )
        if product is None or product.stock_quantity < quantity:
            available = product.stock_quantity if product is not None else 0
            raise InsufficientStockError(product_id, quantity, available)
        product.stock_quantity -= quantity
        cache_delete(tenant_cache_key(f"product:{product.id}"))
        cache_delete_prefix(tenant_cache_key("products:list:"))
        cache_delete_prefix(tenant_cache_key("products:list:"))

    def release_stock(self, product_id: int, quantity: int) -> None:
        """Increments stock back (order cancellation). Also does not commit — see note above."""
        product = self.db.scalar(
            select(Product)
            .where(
                Product.id == product_id,
                Product.tenant_id == get_required_tenant_id(),
                Product.is_deleted.is_(False),
            )
            .with_for_update()
        )
        if product is not None:
            product.stock_quantity += quantity
            cache_delete(tenant_cache_key(f"product:{product.id}"))
