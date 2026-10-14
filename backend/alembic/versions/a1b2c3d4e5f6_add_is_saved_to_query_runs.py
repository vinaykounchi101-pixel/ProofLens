"""add is_saved to query_runs

Revision ID: a1b2c3d4e5f6
Revises: 9cc15fb98728
Create Date: 2026-10-14 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '9cc15fb98728'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    # Check if column already exists
    if conn.dialect.name == "postgresql":
        op.execute("ALTER TABLE query_runs ADD COLUMN IF NOT EXISTS is_saved BOOLEAN DEFAULT TRUE;")
    else:
        with op.batch_alter_table('query_runs', schema=None) as batch_op:
            batch_op.add_column(sa.Column('is_saved', sa.Boolean(), server_default='1', nullable=False))


def downgrade() -> None:
    with op.batch_alter_table('query_runs', schema=None) as batch_op:
        batch_op.drop_column('is_saved')
