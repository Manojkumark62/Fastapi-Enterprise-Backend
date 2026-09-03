"""FileRecord model — uploaded documents, owned by a User."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin
from utils.soft_delete_mixin import SoftDeleteMixin

if TYPE_CHECKING:
    from models.user import User


class FileRecord(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True)
    uploaded_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)

    uploaded_by: Mapped["User"] = relationship(back_populates="files")

    def __repr__(self) -> str:
        return f"<FileRecord id={self.id} filename={self.original_filename!r}>"
