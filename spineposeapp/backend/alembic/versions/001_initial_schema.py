"""initial_schema

Revision ID: 001_initial
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

gender_enum = postgresql.ENUM("male", "female", "other", name="gender_enum", create_type=True)
risk_level_enum = postgresql.ENUM(
    "normal", "monitor", "elevated", name="risk_level_enum", create_type=True
)
scan_status_enum = postgresql.ENUM(
    "pending", "processing", "completed", "failed", name="scan_status_enum", create_type=True
)

# Column references — types created above; avoid duplicate CREATE TYPE on create_table
gender_enum_col = postgresql.ENUM(
    "male", "female", "other", name="gender_enum", create_type=False
)
risk_level_enum_col = postgresql.ENUM(
    "normal", "monitor", "elevated", name="risk_level_enum", create_type=False
)
scan_status_enum_col = postgresql.ENUM(
    "pending", "processing", "completed", "failed", name="scan_status_enum", create_type=False
)


def upgrade() -> None:
    gender_enum.create(op.get_bind(), checkfirst=True)
    risk_level_enum.create(op.get_bind(), checkfirst=True)
    scan_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "doctors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("specialty", sa.String(100), nullable=True),
        sa.Column("license_number", sa.String(100), nullable=True),
        sa.Column("clinic_name", sa.String(200), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_doctors_email", "doctors", ["email"], unique=True)

    op.create_table(
        "patients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("gender", gender_enum_col, nullable=False),
        sa.Column("height_cm", sa.Float(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("medical_record_number", sa.String(100), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("emergency_contact_name", sa.String(200), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(50), nullable=True),
        sa.Column("referring_physician", sa.String(200), nullable=True),
        sa.Column("primary_diagnosis", sa.String(500), nullable=True),
        sa.Column("medical_notes", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column(
            "risk_level",
            risk_level_enum_col,
            nullable=False,
            server_default="normal",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctors.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("doctor_id", "medical_record_number", name="uq_patients_doctor_mrn"),
    )
    op.create_index("ix_patients_doctor_id", "patients", ["doctor_id"])

    op.create_table(
        "scans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", scan_status_enum_col, nullable=False),
        sa.Column("capture_device", sa.String(200), nullable=True),
        sa.Column("camera_height_cm", sa.Float(), nullable=True),
        sa.Column("camera_distance_cm", sa.Float(), nullable=True),
        sa.Column("patient_height_cm", sa.Float(), nullable=False),
        sa.Column("patient_weight_kg", sa.Float(), nullable=False),
        sa.Column("detector_model", sa.String(50), nullable=False),
        sa.Column("raw_frames_prefix", sa.String(500), nullable=True),
        sa.Column("keypoints_json", postgresql.JSONB(), nullable=True),
        sa.Column("metrics_json", postgresql.JSONB(), nullable=True),
        sa.Column("digital_twin_url", sa.String(500), nullable=True),
        sa.Column("overall_risk", risk_level_enum_col, nullable=True),
        sa.Column("progress_message", sa.String(500), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctors.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_scans_patient_id", "scans", ["patient_id"])
    op.create_index("ix_scans_doctor_id", "scans", ["doctor_id"])
    op.create_index("ix_scans_status", "scans", ["status"])
    op.create_index("ix_scans_created_at", "scans", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_scans_created_at", table_name="scans")
    op.drop_index("ix_scans_status", table_name="scans")
    op.drop_index("ix_scans_doctor_id", table_name="scans")
    op.drop_index("ix_scans_patient_id", table_name="scans")
    op.drop_table("scans")
    op.drop_index("ix_patients_doctor_id", table_name="patients")
    op.drop_table("patients")
    op.drop_index("ix_doctors_email", table_name="doctors")
    op.drop_table("doctors")
    scan_status_enum.drop(op.get_bind(), checkfirst=True)
    risk_level_enum.drop(op.get_bind(), checkfirst=True)
    gender_enum.drop(op.get_bind(), checkfirst=True)
