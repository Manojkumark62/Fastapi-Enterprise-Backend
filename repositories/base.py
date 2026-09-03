"""Small SQLAlchemy repository primitives shared by resource services."""

from collections.abc import Sequence
from contextlib import contextmanager
from collections.abc import Iterator
from typing import Generic, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import Session


ModelT = TypeVar("ModelT")


class Repository(Generic[ModelT]):
    """CRUD adapter that keeps query construction out of route handlers."""

    def __init__(self, db: Session, model: type[ModelT]):
        self.db = db
        self.model = model

    def get(self, entity_id: int) -> ModelT | None:
        return self.db.get(self.model, entity_id)

    def find(self, statement: Select) -> Sequence[ModelT]:
        return self.db.scalars(statement).all()

    def list(self, *, limit: int | None = None, offset: int = 0) -> Sequence[ModelT]:
        statement = select(self.model).offset(offset)
        if limit is not None:
            statement = statement.limit(limit)
        return self.find(statement)

    def add(self, entity: ModelT) -> ModelT:
        self.db.add(entity)
        self.db.flush()
        return entity

    def update(self, entity: ModelT, values: dict) -> ModelT:
        """Apply validated values and flush without owning the transaction."""
        for field, value in values.items():
            setattr(entity, field, value)
        self.db.flush()
        return entity

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    @contextmanager
    def transaction(self) -> Iterator[Session]:
        """Commit on success and roll back on any error."""
        try:
            yield self.db
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def delete(self, entity: ModelT) -> None:
        self.db.delete(entity)
        self.db.flush()
