"""Advanced features router for session management, restore, and audit queries (Modules 30, 35, 56)."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime

from dependencies.auth import get_current_active_user, get_current_superuser
from dependencies.db import get_db
from dependencies.tenant import get_required_tenant_id
from models.user import User
from models.customer import Customer
from models.product import Product
from models.employee import Employee
from models.order import Order
from models.task import Task
from models.session import UserSession
from models.audit_log import AuditLog
from services.session_management_service import SessionManagementService
from services.audit_query_service import AuditQueryService
from services.order_filter_service import OrderFilterService
from exceptions.custom_exceptions import AppException
from schemas.common import PaginatedResponse, MessageResponse

router = APIRouter(tags=["Advanced features"])


# ============================================================================
# Session Management (Module 30)
# ============================================================================

@router.get("/sessions", response_model=list[dict])
def list_active_sessions(
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_active_user),
):
    """List all active sessions for the current user."""
    sessions = SessionManagementService.list_active_sessions(db, actor.id)
    return [
        {
            "id": s.id,
            "ip_address": s.ip_address,
            "user_agent": s.user_agent,
            "is_active": s.is_active,
            "last_active_at": s.last_active_at.isoformat() if s.last_active_at else None,
            "expires_at": s.expires_at.isoformat() if s.expires_at else None,
        }
        for s in sessions
    ]


@router.delete("/sessions/{session_id}", status_code=204)
def revoke_session(
    session_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_active_user),
):
    """Revoke a specific session (logout that device)."""
    try:
        SessionManagementService.revoke_session(db, session_id, actor.id)
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


# ============================================================================
# Soft-Delete Restoration (Module 35, 19)
# ============================================================================

@router.patch("/customers/{customer_id}/restore", response_model=dict, status_code=200)
def restore_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    """Restore a soft-deleted customer."""
    customer = db.scalar(select(Customer).where(
        Customer.id == customer_id,
        Customer.tenant_id == get_required_tenant_id(),
    ))
    if not customer or not customer.is_deleted:
        raise HTTPException(status_code=404, detail="Customer not found or not deleted")
    customer.restore()
    db.commit()
    db.refresh(customer)
    return {"id": customer.id, "is_deleted": customer.is_deleted, "message": "Customer restored"}


@router.patch("/products/{product_id}/restore", response_model=dict, status_code=200)
def restore_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    """Restore a soft-deleted product."""
    product = db.scalar(select(Product).where(
        Product.id == product_id,
        Product.tenant_id == get_required_tenant_id(),
    ))
    if not product or not product.is_deleted:
        raise HTTPException(status_code=404, detail="Product not found or not deleted")
    product.restore()
    db.commit()
    db.refresh(product)
    return {"id": product.id, "is_deleted": product.is_deleted, "message": "Product restored"}


@router.patch("/employees/{employee_id}/restore", response_model=dict, status_code=200)
def restore_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    """Restore a soft-deleted employee."""
    employee = db.scalar(select(Employee).where(
        Employee.id == employee_id,
        Employee.tenant_id == get_required_tenant_id(),
    ))
    if not employee or not employee.is_deleted:
        raise HTTPException(status_code=404, detail="Employee not found or not deleted")
    employee.restore()
    db.commit()
    db.refresh(employee)
    return {"id": employee.id, "is_deleted": employee.is_deleted, "message": "Employee restored"}


@router.patch("/orders/{order_id}/restore", response_model=dict, status_code=200)
def restore_order(
    order_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    """Restore a soft-deleted order."""
    order = db.scalar(select(Order).where(
        Order.id == order_id,
        Order.tenant_id == get_required_tenant_id(),
    ))
    if not order or not order.is_deleted:
        raise HTTPException(status_code=404, detail="Order not found or not deleted")
    order.restore()
    db.commit()
    db.refresh(order)
    return {"id": order.id, "is_deleted": order.is_deleted, "message": "Order restored"}


@router.patch("/tasks/{task_id}/restore", response_model=dict, status_code=200)
def restore_task(
    task_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    """Restore a soft-deleted task."""
    task = db.scalar(select(Task).where(
        Task.id == task_id,
        Task.tenant_id == get_required_tenant_id(),
    ))
    if not task or not task.is_deleted:
        raise HTTPException(status_code=404, detail="Task not found or not deleted")
    task.restore()
    db.commit()
    db.refresh(task)
    return {"id": task.id, "is_deleted": task.is_deleted, "message": "Task restored"}


# ============================================================================
# Advanced Audit Queries (Modules 56-57)
# ============================================================================

@router.get("/audit-logs/advanced", response_model=dict)
def list_audit_logs_advanced(
    actor_id: int | None = Query(None),
    entity_type: str | None = Query(None),
    action: str | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """List audit logs with advanced filtering by date, entity type, action, etc."""
    logs, total = AuditQueryService.list_audit_logs_advanced(
        db,
        actor_id=actor_id,
        entity_type=entity_type,
        action=action,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
    return {
        "items": [
            {
                "id": log.id,
                "actor_id": log.actor_id,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "timestamp": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/history/{entity_type}/{entity_id}/timeline", response_model=dict)
def get_entity_timeline(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """Get complete timeline of changes to an entity."""
    timeline = AuditQueryService.get_entity_timeline(db, entity_type, entity_id)
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "timeline": timeline,
    }


# ============================================================================
# Advanced Order Filtering (Modules 38-40)
# ============================================================================

@router.get("/orders/search", response_model=dict)
def search_orders(
    customer_id: int | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_desc: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """Search and filter orders with sorting and pagination."""
    orders, total = OrderFilterService.list_orders_advanced(
        db,
        customer_id=customer_id,
        status=status,
        search=search,
        sort_by=sort_by,
        sort_desc=sort_desc,
        skip=skip,
        limit=limit,
    )
    return {
        "items": [
            {
                "id": o.id,
                "order_number": o.order_number,
                "customer_id": o.customer_id,
                "status": o.status,
                "total_amount": str(o.total_amount),
                "created_at": o.created_at.isoformat(),
            }
            for o in orders
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }
