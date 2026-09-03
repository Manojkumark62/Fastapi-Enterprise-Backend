"""User service — admin-facing CRUD over users (registration itself lives in auth_service.py)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from dependencies.pagination import PaginationParams
from models.user import User
from schemas.user import UserUpdateRequest
from utils.query_filters import exclude_deleted


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        user = self.db.get(User, user_id)
        if user is not None and user.is_deleted:
            return None
        return user

    def list_users(self, pagination: PaginationParams) -> tuple[list[User], int]:
        base = exclude_deleted(select(User), User)

        total = self.db.execute(
            select(func.count()).select_from(base.subquery())
        ).scalar_one()

        rows = self.db.execute(
            base.order_by(User.id).offset(pagination.offset).limit(pagination.limit)
        ).scalars().all()

        return list(rows), total

    def update(self, user_id: int, payload: UserUpdateRequest) -> User | None:
        user = self.get_by_id(user_id)
        if user is None:
            return None

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def soft_delete(self, user_id: int) -> bool:
        user = self.get_by_id(user_id)
        if user is None:
            return False
        user.soft_delete()
        self.db.commit()
        return True
