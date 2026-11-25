"""Add hashed_password and role to users table

Revision ID: c1f4e92a8b3d
Revises: 9aa14a4442a2
Create Date: 2026-11-25 09:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1f4e92a8b3d'
down_revision: Union[str, Sequence[str], None] = '9aa14a4442a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('hashed_password', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('role', sa.String(length=50), nullable=False, server_default='alumnus'))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('role')
        batch_op.drop_column('hashed_password')
