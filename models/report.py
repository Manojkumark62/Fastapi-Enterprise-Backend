"""Report model — persisted report runs (Modules 39/60)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.user import User


class Report(Base, TimestampMixin):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    generated_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    parameters: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON text of filters used
    result_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="completed", nullable=False)

    generated_by: Mapped["User | None"] = relationship()

    def __repr__(self) -> str:
        return f"<Report id={self.id} name={self.name!r} type={self.report_type!r}>"
