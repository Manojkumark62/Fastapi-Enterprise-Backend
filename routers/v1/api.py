"""
Aggregates every v1 router into one. main.py includes only this, not each
sub-router individually — adding a new resource means one line here, not
a change to main.py.
"""

from fastapi import APIRouter

from routers.v1 import auth, business, customers, employees, enterprise, orders, payments, permissions, products, roles, users, advanced_features

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(roles.router)
api_router.include_router(permissions.router)
api_router.include_router(employees.router)
api_router.include_router(customers.router)
api_router.include_router(products.router)
# Register specific paths such as /orders/search before /orders/{order_id}.
api_router.include_router(advanced_features.router)
api_router.include_router(orders.router)
api_router.include_router(payments.router)
api_router.include_router(enterprise.router)
api_router.include_router(business.router)
