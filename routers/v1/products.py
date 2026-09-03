from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.constants import PermissionCodeEnum
from core.cache import cache_delete, cache_delete_prefix, cache_get, cache_set, tenant_cache_key
from dependencies.auth import get_current_active_user
from dependencies.db import get_db
from dependencies.pagination import PaginationParams, build_paginated_response, get_pagination_params
from dependencies.request_validation import ProductFilters, get_product_filters
from dependencies.permissions import require_permission
from schemas.common import MessageResponse, PaginatedResponse
from schemas.common import BulkOperationResult
from schemas.product import ProductBulkUpdateRequest, ProductCreateRequest, ProductResponse, ProductUpdateRequest
from services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreateRequest,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.CREATE_PRODUCT)),
):
    product = ProductService(db).create(payload)
    cache_delete(tenant_cache_key(f"product:{product.id}"))
    cache_delete_prefix(tenant_cache_key("products:list:"))
    return product


@router.get("", response_model=PaginatedResponse[ProductResponse])
def list_products(
    filters: ProductFilters = Depends(get_product_filters),
    pagination: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    cache_key = tenant_cache_key(
        f"products:list:{filters.category}:{filters.categories}:{filters.name}:"
        f"{filters.min_price}:{filters.max_price}:{filters.sort_by}:{filters.sort_order}:"
        f"{pagination.page}:{pagination.page_size}"
    )
    cached = cache_get(cache_key)
    if cached is not None:
        return cached
    items, total = ProductService(db).list_products(pagination, filters=filters)
    response = build_paginated_response(items, total, pagination)
    cache_set(cache_key, response)
    return response


@router.post("/bulk-delete", response_model=BulkOperationResult)
def bulk_delete_products(
    product_ids: list[int],
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.DELETE_PRODUCT)),
):
    succeeded = ProductService(db).bulk_delete(product_ids)
    cache_delete(*(tenant_cache_key(f"product:{product_id}") for product_id in product_ids))
    cache_delete_prefix(tenant_cache_key("products:list:"))
    return BulkOperationResult(succeeded=succeeded, failed=len(product_ids) - succeeded, errors=[])


@router.post("/bulk", response_model=list[ProductResponse], status_code=status.HTTP_201_CREATED)
def bulk_create_products(
    payloads: list[ProductCreateRequest] = Body(..., min_length=1, max_length=100),
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.CREATE_PRODUCT)),
):
    return ProductService(db).bulk_create(payloads)


@router.patch("/bulk", response_model=list[ProductResponse])
def bulk_update_products(
    payloads: list[ProductBulkUpdateRequest] = Body(..., min_length=1, max_length=100),
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.UPDATE_PRODUCT)),
):
    try:
        products = ProductService(db).bulk_update(payloads)
        cache_delete(*(tenant_cache_key(f"product:{product.id}") for product in products))
        cache_delete_prefix(tenant_cache_key("products:list:"))
        return products
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db), _: object = Depends(get_current_active_user)):
    cache_key = tenant_cache_key(f"product:{product_id}")
    cached = cache_get(cache_key)
    if cached is not None:
        return cached
    product = ProductService(db).get_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    cache_set(cache_key, ProductResponse.model_validate(product).model_dump(mode="json"))
    return product


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    payload: ProductUpdateRequest,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.UPDATE_PRODUCT)),
):
    product = ProductService(db).update(product_id, payload)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    cache_delete(tenant_cache_key(f"product:{product_id}"))
    cache_delete_prefix(tenant_cache_key("products:list:"))
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def replace_product(
    product_id: int,
    payload: ProductCreateRequest,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.UPDATE_PRODUCT)),
):
    product = ProductService(db).replace(product_id, payload)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    cache_delete(tenant_cache_key(f"product:{product_id}"))
    cache_delete_prefix(tenant_cache_key("products:list:"))
    return product


@router.delete("/{product_id}", response_model=MessageResponse)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission(PermissionCodeEnum.DELETE_PRODUCT)),
):
    if not ProductService(db).soft_delete(product_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    cache_delete(tenant_cache_key(f"product:{product_id}"))
    cache_delete_prefix(tenant_cache_key("products:list:"))
    return MessageResponse(message="Product deleted")


