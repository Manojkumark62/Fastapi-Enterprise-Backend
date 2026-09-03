from sqlalchemy import func, select
from sqlalchemy.orm import Session

from dependencies.pagination import PaginationParams
from dependencies.tenant import get_required_tenant_id
from models.employee import Employee
from schemas.employee import EmployeeCreateRequest, EmployeeUpdateRequest
from utils.query_filters import exclude_deleted


class EmployeeService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: EmployeeCreateRequest) -> Employee:
        employee = Employee(**payload.model_dump(), tenant_id=get_required_tenant_id())
        self.db.add(employee)
        self.db.commit()
        self.db.refresh(employee)
        return employee

    def get_by_id(self, employee_id: int) -> Employee | None:
        employee = self.db.scalar(
            select(Employee).where(Employee.id == employee_id, Employee.tenant_id == get_required_tenant_id())
        )
        if employee is not None and employee.is_deleted:
            return None
        return employee

    def list_employees(self, pagination: PaginationParams) -> tuple[list[Employee], int]:
        base = exclude_deleted(select(Employee), Employee)
        base = base.where(Employee.tenant_id == get_required_tenant_id())
        total = self.db.execute(select(func.count()).select_from(base.subquery())).scalar_one()
        rows = self.db.execute(
            base.order_by(Employee.id).offset(pagination.offset).limit(pagination.limit)
        ).scalars().all()
        return list(rows), total

    def update(self, employee_id: int, payload: EmployeeUpdateRequest) -> Employee | None:
        employee = self.get_by_id(employee_id)
        if employee is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(employee, field, value)
        self.db.commit()
        self.db.refresh(employee)
        return employee

    def soft_delete(self, employee_id: int) -> bool:
        employee = self.get_by_id(employee_id)
        if employee is None:
            return False
        employee.soft_delete()
        self.db.commit()
        return True
