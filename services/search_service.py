"""Database-backed search boundary, replaceable by an external index later."""

from sqlalchemy import Select
from sqlalchemy.orm import DeclarativeBase

from utils.query_filters_v2 import with_search


class SearchService:
    """Build portable search statements without coupling callers to SQLAlchemy details."""

    @staticmethod
    def apply(statement: Select, model: type[DeclarativeBase], query: str | None, fields: list[str]) -> Select:
        return with_search(statement, model, query, fields)
