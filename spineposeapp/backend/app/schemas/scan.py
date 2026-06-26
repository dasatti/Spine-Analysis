import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.patient import RiskLevel
from app.models.scan import ScanStatus


class ScanCreateResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    status: ScanStatus
    detector_model: str
    created_at: datetime


class ScanStatusResponse(BaseModel):
    id: uuid.UUID
    status: ScanStatus
    progress_message: str | None
    detector_model: str
    started_at: datetime | None
    completed_at: datetime | None


class FrameUrls(BaseModel):
    front: str | None = None
    side: str | None = None
    back: str | None = None
    adams: str | None = None
    face: str | None = None


class PatientBrief(BaseModel):
    first_name: str
    last_name: str


class ScanDetailResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    patient: PatientBrief
    status: ScanStatus
    detector_model: str
    capture_device: str | None
    camera_height_cm: float | None
    camera_distance_cm: float | None
    patient_height_cm: float
    patient_weight_kg: float
    overall_risk: RiskLevel | None
    digital_twin_url: str | None
    metrics: dict | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    frame_urls: FrameUrls = Field(default_factory=FrameUrls)


class ScanListItem(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    patient_name: str
    status: ScanStatus
    detector_model: str
    overall_risk: RiskLevel | None
    created_at: datetime
    completed_at: datetime | None


class ScanListResponse(BaseModel):
    items: list[ScanListItem]
    total: int
    page: int
    page_size: int
    pages: int
