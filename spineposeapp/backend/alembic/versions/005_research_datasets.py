"""Add research_datasets table and link dataset_items to datasets."""

from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_research_datasets"
down_revision: Union[str, None] = "004_dataset_items"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_DATASET_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")


def upgrade() -> None:
    op.create_table(
        "research_datasets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "created_by_doctor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("doctors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_research_datasets_name", "research_datasets", ["name"])
    op.create_index("ix_research_datasets_created_by_doctor_id", "research_datasets", ["created_by_doctor_id"])
    op.create_index("ix_research_datasets_created_at", "research_datasets", ["created_at"])

    op.execute(
        sa.text(
            """
            INSERT INTO research_datasets (id, name, created_at, updated_at)
            VALUES (:id, 'Default Dataset', NOW(), NOW())
            """
        ).bindparams(id=DEFAULT_DATASET_ID)
    )

    op.add_column(
        "dataset_items",
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute(
        sa.text("UPDATE dataset_items SET dataset_id = :dataset_id").bindparams(
            dataset_id=DEFAULT_DATASET_ID
        )
    )
    op.alter_column("dataset_items", "dataset_id", nullable=False)
    op.create_foreign_key(
        "fk_dataset_items_dataset_id",
        "dataset_items",
        "research_datasets",
        ["dataset_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_dataset_items_dataset_id", "dataset_items", ["dataset_id"])


def downgrade() -> None:
    op.drop_index("ix_dataset_items_dataset_id", table_name="dataset_items")
    op.drop_constraint("fk_dataset_items_dataset_id", "dataset_items", type_="foreignkey")
    op.drop_column("dataset_items", "dataset_id")
    op.drop_table("research_datasets")
