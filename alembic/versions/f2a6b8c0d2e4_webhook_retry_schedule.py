"""Add scheduled webhook retry timestamp."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2a6b8c0d2e4"
down_revision: Union[str, Sequence[str], None] = "e1f4a6b8c0d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("webhook_events", sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_webhook_events_next_attempt_at", "webhook_events", ["next_attempt_at"])


def downgrade() -> None:
    op.drop_index("ix_webhook_events_next_attempt_at", table_name="webhook_events")
    op.drop_column("webhook_events", "next_attempt_at")