import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DatasetPoseType(str, enum.Enum):
    front = "front"
    side = "side"
    back = "back"
    adams = "adams"
    face = "face"


class DatasetItemStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class DatasetItem(Base):
    __tablename__ = "dataset_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_by_doctor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("doctors.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    pose_type: Mapped[DatasetPoseType] = mapped_column(
        Enum(DatasetPoseType, name="dataset_pose_type_enum", native_enum=True),
        index=True,
        nullable=False,
    )
    detector_model: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    status: Mapped[DatasetItemStatus] = mapped_column(
        Enum(DatasetItemStatus, name="dataset_item_status_enum", native_enum=True),
        index=True,
        nullable=False,
        default=DatasetItemStatus.pending,
    )
    image_key: Mapped[str] = mapped_column(String(500), nullable=False)
    image_content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    keypoints_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    inference_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
