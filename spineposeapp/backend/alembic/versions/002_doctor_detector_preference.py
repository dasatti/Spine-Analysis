"""doctor_detector_preference

Revision ID: 002_detector_pref
Revises: 001_initial
Create Date: 2026-06-26 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_detector_pref"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "doctors",
        sa.Column("preferred_detector_model", sa.String(50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("doctors", "preferred_detector_model")
