"""add_is_active_to_hotels

Revision ID: 167861b13ecf
Revises: 5b208589417a
Create Date: 2026-07-04 08:49:10.605739

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '167861b13ecf'
down_revision: Union[str, Sequence[str], None] = '5b208589417a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('hotels', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))


def downgrade() -> None:
    op.drop_column('hotels', 'is_active')