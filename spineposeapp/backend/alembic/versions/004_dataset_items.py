"""dataset_items

Revision ID: 004_dataset_items
Revises: 003_doctor_role
Create Date: 2026-07-07 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_dataset_items"
down_revision: Union[str, None] = "003_doctor_role"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

pose_type_enum = postgresql.ENUM(
    "front", "side", "back", "adams", "face", name="dataset_pose_type_enum", create_type=True
)
status_enum = postgresql.ENUM(
    "pending", "processing", "ready", "failed", name="dataset_item_status_enum", create_type=True
)
pose_type_col = postgresql.ENUM(
    "front", "side", "back", "adams", "face", name="dataset_pose_type_enum", create_type=False
)
status_col = postgresql.ENUM(
    "pending", "processing", "ready", "failed", name="dataset_item_status_enum", create_type=False
)


def upgrade() -> None:
    pose_type_enum.create(op.get_bind(), checkfirst=True)
    status_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "dataset_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_by_doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True),
        sa.Column("pose_type", pose_type_col, nullable=False),
        sa.Column("detector_model", sa.String(50), nullable=False),
        sa.Column("status", status_col, nullable=False, server_default="pending"),
        sa.Column("image_key", sa.String(500), nullable=False),
        sa.Column("image_content_type", sa.String(100), nullable=True),
        sa.Column("original_filename", sa.String(255), nullable=True),
        sa.Column("keypoints_json", postgresql.JSONB, nullable=True),
        sa.Column("inference_error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_dataset_items_created_by_doctor_id", "dataset_items", ["created_by_doctor_id"])
    op.create_index("ix_dataset_items_pose_type", "dataset_items", ["pose_type"])
    op.create_index("ix_dataset_items_detector_model", "dataset_items", ["detector_model"])
    op.create_index("ix_dataset_items_status", "dataset_items", ["status"])
    op.create_index("ix_dataset_items_created_at", "dataset_items", ["created_at"])


def downgrade() -> None:
    op.drop_table("dataset_items")
    status_enum.drop(op.get_bind(), checkfirst=True)
    pose_type_enum.drop(op.get_bind(), checkfirst=True)
