"""Multi-tenant context and ownership enforcement."""

from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.user import User


class Tenant(Base, TimestampMixin):
    """
    Tenant/organization entity (Module 34-36).
    Each user can belong to one or more tenants.
    """
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    owner: Mapped["User"] = relationship(foreign_keys=[owner_id])

    def __repr__(self) -> str:
        return f"<Tenant id={self.id} name={self.name!r}>"
