import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.patient import RiskLevel


class ScanStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    doctor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("doctors.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    status: Mapped[ScanStatus] = mapped_column(
        Enum(ScanStatus, name="scan_status_enum", native_enum=True),
        index=True,
        nullable=False,
    )
    capture_device: Mapped[str | None] = mapped_column(String(200), nullable=True)
    camera_height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    camera_distance_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    patient_height_cm: Mapped[float] = mapped_column(Float, nullable=False)
    patient_weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    detector_model: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_frames_prefix: Mapped[str | None] = mapped_column(String(500), nullable=True)
    keypoints_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metrics_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    digital_twin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    overall_risk: Mapped[RiskLevel | None] = mapped_column(
        Enum(RiskLevel, name="risk_level_enum", native_enum=True, create_type=False),
        nullable=True,
    )
    progress_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    patient = relationship("Patient", back_populates="scans")
    doctor = relationship("Doctor", back_populates="scans")
