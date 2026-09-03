"""Add tenant ownership to domain records.

Revision ID: d9a3f0b2c4e5
Revises: c8f2e9a1b3d4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d9a3f0b2c4e5"
down_revision: Union[str, Sequence[str], None] = "c8f2e9a1b3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = ("customers", "employees", "products", "orders", "tasks", "payments")


def upgrade() -> None:
    # Existing installations receive the first tenant as a compatibility
    # backfill; new records are always written with the active tenant.
    connection = op.get_bind()
    default_tenant = connection.execute(sa.text("SELECT id FROM tenants ORDER BY id LIMIT 1")).scalar()
    for table in _TABLES:
        op.add_column(table, sa.Column("tenant_id", sa.Integer(), nullable=True))
        if default_tenant is not None:
            op.execute(sa.text(f"UPDATE {table} SET tenant_id = :tenant_id WHERE tenant_id IS NULL").bindparams(tenant_id=default_tenant))
        op.create_index(f"ix_{table}_tenant_id", table, ["tenant_id"])
        op.create_foreign_key(
            f"fk_{table}_tenant_id_tenants",
            table,
            "tenants",
            ["tenant_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    for table in reversed(_TABLES):
        op.drop_constraint(f"fk_{table}_tenant_id_tenants", table, type_="foreignkey")
        op.drop_index(f"ix_{table}_tenant_id", table_name=table)
        op.drop_column(table, "tenant_id")
