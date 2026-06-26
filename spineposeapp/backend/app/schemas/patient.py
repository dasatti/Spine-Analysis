import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.patient import Gender, RiskLevel
from app.models.scan import ScanStatus


class PatientCreateRequest(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    gender: Gender
    height_cm: float
    weight_kg: float
    medical_record_number: str | None = None
    phone: str | None = None
    email: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    referring_physician: str | None = None
    primary_diagnosis: str | None = None
    medical_notes: str | None = None


class PatientUpdateRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    gender: Gender | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    medical_record_number: str | None = None
    phone: str | None = None
    email: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    referring_physician: str | None = None
    primary_diagnosis: str | None = None
    medical_notes: str | None = None


class PatientListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str
    medical_record_number: str | None
    date_of_birth: date
    gender: Gender
    height_cm: float
    weight_kg: float
    risk_level: RiskLevel
    scan_count: int = 0
    last_scan_at: datetime | None = None
    created_at: datetime


class PatientListResponse(BaseModel):
    items: list[PatientListItem]
    total: int
    page: int
    page_size: int
    pages: int


class ScanSummary(BaseModel):
    id: uuid.UUID
    status: ScanStatus
    created_at: datetime
    detector_model: str
    overall_risk: RiskLevel | None
    metrics_count: int = 0


class PatientDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    doctor_id: uuid.UUID
    first_name: str
    last_name: str
    date_of_birth: date
    gender: Gender
    height_cm: float
    weight_kg: float
    medical_record_number: str | None
    phone: str | None
    email: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    referring_physician: str | None
    primary_diagnosis: str | None
    medical_notes: str | None
    avatar_url: str | None
    risk_level: RiskLevel
    is_active: bool
    created_at: datetime
    updated_at: datetime
    scan_count: int = 0
    last_scan_at: datetime | None = None
    recent_scans: list[ScanSummary] = Field(default_factory=list)
