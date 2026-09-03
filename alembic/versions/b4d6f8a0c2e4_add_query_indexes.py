"""Add indexes for tenant-scoped high-volume queries."""

from typing import Sequence, Union

from alembic import op


revision: str = "b4d6f8a0c2e4"
down_revision: Union[str, Sequence[str], None] = "a3c5e7f9b1d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_products_tenant_category", "products", ["tenant_id", "category"])
    op.create_index(
        "ix_orders_tenant_status_created", "orders", ["tenant_id", "status", "created_at"]
    )
    op.create_index(
        "ix_notifications_user_read_created",
        "notifications",
        ["user_id", "is_read", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_user_read_created", table_name="notifications")
    op.drop_index("ix_orders_tenant_status_created", table_name="orders")
    op.drop_index("ix_products_tenant_category", table_name="products")
