"""add missing foreign keys to hotels and bookings

Revision ID: ca254b33e1ae
Revises: 49205fac1d20
Create Date: 2026-07-06 14:38:03.241568

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca254b33e1ae'
down_revision: Union[str, Sequence[str], None] = '49205fac1d20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.create_foreign_key(
            'fk_bookings_user_id_users', 'users', ['user_id'], ['id']
        )

    with op.batch_alter_table('hotels', schema=None) as batch_op:
        batch_op.create_foreign_key(
            'fk_hotels_owner_id_users', 'users', ['owner_id'], ['id']
        )


def downgrade() -> None:
    with op.batch_alter_table('hotels', schema=None) as batch_op:
        batch_op.drop_constraint('fk_hotels_owner_id_users', type_='foreignkey')

    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.drop_constraint('fk_bookings_user_id_users', type_='foreignkey')