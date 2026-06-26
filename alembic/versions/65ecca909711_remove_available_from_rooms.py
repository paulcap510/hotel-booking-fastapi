"""Remove available from rooms

Revision ID: 65ecca909711
Revises: d142cb5a14ca
Create Date: 2026-06-25 14:17:50.851389

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65ecca909711'
down_revision: Union[str, Sequence[str], None] = 'd142cb5a14ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("rooms") as batch_op:
        batch_op.drop_column("available")

def downgrade() -> None:
    with op.batch_alter_table("rooms") as batch_op:
        batch_op.add_column(sa.Column("available", sa.Boolean(), nullable=True))