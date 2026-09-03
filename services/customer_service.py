from sqlalchemy import func, select
from sqlalchemy.orm import Session

from dependencies.pagination import PaginationParams
from dependencies.tenant import get_required_tenant_id
from models.customer import Customer
from repositories import Repository
from schemas.customer import CustomerCreateRequest, CustomerUpdateRequest
from utils.query_filters import exclude_deleted


class CustomerService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = Repository(db, Customer)

    def create(self, payload: CustomerCreateRequest) -> Customer:
        customer = Customer(**payload.model_dump(), tenant_id=get_required_tenant_id())
        self.repository.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def get_by_id(self, customer_id: int) -> Customer | None:
        customer = self.db.scalar(
            select(Customer).where(Customer.id == customer_id, Customer.tenant_id == get_required_tenant_id())
        )
        if customer is not None and customer.is_deleted:
            return None
        return customer

    def list_customers(self, pagination: PaginationParams) -> tuple[list[Customer], int]:
        base = exclude_deleted(select(Customer), Customer)
        base = base.where(Customer.tenant_id == get_required_tenant_id())
        total = self.db.execute(select(func.count()).select_from(base.subquery())).scalar_one()
        rows = self.db.execute(
            base.order_by(Customer.id).offset(pagination.offset).limit(pagination.limit)
        ).scalars().all()
        return list(rows), total

    def update(self, customer_id: int, payload: CustomerUpdateRequest) -> Customer | None:
        customer = self.get_by_id(customer_id)
        if customer is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(customer, field, value)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def soft_delete(self, customer_id: int) -> bool:
        customer = self.get_by_id(customer_id)
        if customer is None:
            return False
        customer.soft_delete()
        self.db.commit()
        return True
