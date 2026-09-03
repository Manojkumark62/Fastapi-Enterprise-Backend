"""Add payment idempotency and refund tracking."""

from alembic import op
import sqlalchemy as sa

revision = "b7f8e9d0c1a2"
down_revision = "81962d37e3f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("payments", sa.Column("idempotency_key", sa.String(length=255), nullable=True))
    op.add_column("payments", sa.Column("refunded_amount", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.execute("UPDATE payments SET idempotency_key = CONCAT('legacy-', id)")
    op.alter_column("payments", "idempotency_key", nullable=False)
    op.create_index("ix_payments_idempotency_key", "payments", ["idempotency_key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_payments_idempotency_key", table_name="payments")
    op.drop_column("payments", "refunded_amount")
    op.drop_column("payments", "idempotency_key")