"""doctor_role

Revision ID: 003_doctor_role
Revises: 002_detector_pref
Create Date: 2026-07-07 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_doctor_role"
down_revision: Union[str, None] = "002_detector_pref"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "doctors",
        sa.Column("role", sa.String(20), nullable=False, server_default="doctor"),
    )
    op.execute(
        "UPDATE doctors SET role = 'admin' WHERE email = 'dasatti@gmail.com'"
    )


def downgrade() -> None:
    op.drop_column("doctors", "role")
