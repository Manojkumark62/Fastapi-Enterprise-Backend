"""Add database-level value constraints.

Revision ID: e1f4a6b8c0d2
Revises: d9a3f0b2c4e5
"""

from typing import Sequence, Union

from alembic import op


revision: str = "e1f4a6b8c0d2"
down_revision: Union[str, Sequence[str], None] = "d9a3f0b2c4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint("ck_products_price_positive", "products", "price > 0")
    op.create_check_constraint(
        "ck_products_stock_nonnegative", "products", "stock_quantity >= 0"
    )
    op.create_check_constraint(
        "ck_order_items_quantity_positive", "order_items", "quantity > 0"
    )
    op.create_check_constraint(
        "ck_order_items_unit_price_nonnegative", "order_items", "unit_price >= 0"
    )
    op.create_check_constraint("ck_orders_total_nonnegative", "orders", "total_amount >= 0")
    op.create_check_constraint("ck_payments_amount_nonnegative", "payments", "amount >= 0")
    op.create_check_constraint(
        "ck_payments_refunded_nonnegative", "payments", "refunded_amount >= 0"
    )
    op.create_check_constraint(
        "ck_payments_refunded_lte_amount", "payments", "refunded_amount <= amount"
    )


def downgrade() -> None:
    op.drop_constraint("ck_payments_refunded_lte_amount", "payments", type_="check")
    op.drop_constraint("ck_payments_refunded_nonnegative", "payments", type_="check")
    op.drop_constraint("ck_payments_amount_nonnegative", "payments", type_="check")
    op.drop_constraint("ck_orders_total_nonnegative", "orders", type_="check")
    op.drop_constraint("ck_order_items_unit_price_nonnegative", "order_items", type_="check")
    op.drop_constraint("ck_order_items_quantity_positive", "order_items", type_="check")
    op.drop_constraint("ck_products_stock_nonnegative", "products", type_="check")
    op.drop_constraint("ck_products_price_positive", "products", type_="check")