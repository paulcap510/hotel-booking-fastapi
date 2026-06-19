"""change room price to price per night

Revision ID: 8dd7baa6bb1b
Revises: 5d2793bfb1ee
Create Date: 2026-06-19 11:04:32.963055

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8dd7baa6bb1b'
down_revision: Union[str, Sequence[str], None] = '5d2793bfb1ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute(
        """
        UPDATE rooms
        SET price_per_night = 100
        WHERE price_per_night IS NULL
        """
    )

    with op.batch_alter_table('rooms') as batch_op:
        batch_op.alter_column(
            'price_per_night',
            existing_type=sa.Integer(),
            nullable=False
        )

def downgrade() -> None:
    """Downgrade schema."""

    with op.batch_alter_table('rooms') as batch_op:
        batch_op.add_column(
            sa.Column('price', sa.VARCHAR(), nullable=True)
        )

    op.execute(
        """
        UPDATE rooms
        SET price = '$' || price_per_night
        """
    )

    with op.batch_alter_table('rooms') as batch_op:
        batch_op.alter_column(
            'price',
            existing_type=sa.VARCHAR(),
            nullable=False
        )
        batch_op.drop_column('price_per_night')
    """Downgrade schema."""

    with op.batch_alter_table('rooms') as batch_op:
        batch_op.add_column(
            sa.Column('price', sa.VARCHAR(), nullable=True)
        )

    op.execute(
        """
        UPDATE rooms
        SET price = '$' || price_per_night
        """
    )

    with op.batch_alter_table('rooms') as batch_op:
        batch_op.alter_column(
            'price',
            existing_type=sa.VARCHAR(),
            nullable=False
        )
        batch_op.drop_column('price_per_night')