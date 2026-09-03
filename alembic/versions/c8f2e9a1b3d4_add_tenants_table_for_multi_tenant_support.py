"""Add tenants table for multi-tenant support (Module 34-36)

Revision ID: c8f2e9a1b3d4
Revises: b7f8e9d0c1a2
Create Date: 2026-08-25 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8f2e9a1b3d4'
down_revision: Union[str, Sequence[str], None] = 'b7f8e9d0c1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add tenants table."""
    op.create_table(
        'tenants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tenants_name'), 'tenants', ['name'], unique=True)
    op.create_index(op.f('ix_tenants_slug'), 'tenants', ['slug'], unique=True)


def downgrade() -> None:
    """Downgrade schema - remove tenants table."""
    op.drop_index(op.f('ix_tenants_slug'), table_name='tenants')
    op.drop_index(op.f('ix_tenants_name'), table_name='tenants')
    op.drop_table('tenants')
