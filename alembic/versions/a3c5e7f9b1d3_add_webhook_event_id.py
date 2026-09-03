"""Add webhook event IDs for replay protection."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a3c5e7f9b1d3"
down_revision: Union[str, Sequence[str], None] = "f2a6b8c0d2e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("webhook_events", sa.Column("event_id", sa.String(length=255), nullable=True))
    op.execute(sa.text("UPDATE webhook_events SET event_id = CONCAT('legacy-', id) WHERE event_id IS NULL"))
    op.alter_column("webhook_events", "event_id", nullable=False)
    op.create_unique_constraint("uq_webhook_source_event", "webhook_events", ["source", "event_id"])


def downgrade() -> None:
    op.drop_constraint("uq_webhook_source_event", "webhook_events", type_="unique")
    op.drop_column("webhook_events", "event_id")