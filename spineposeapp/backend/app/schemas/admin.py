import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class AdminDoctorListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    specialty: str | None
    clinic_name: str | None
    country: str | None
    city: str | None
    is_active: bool
    role: str
    patient_count: int = 0
    scan_count: int = 0
    created_at: datetime


class AdminDoctorListResponse(BaseModel):
    items: list[AdminDoctorListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminDoctorDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    specialty: str | None
    license_number: str | None
    clinic_name: str | None
    country: str | None
    city: str | None
    bio: str | None
    avatar_url: str | None
    is_active: bool
    role: str
    patient_count: int = 0
    scan_count: int = 0
    created_at: datetime
    updated_at: datetime


class AdminDoctorUpdateRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    specialty: str | None = None
    license_number: str | None = None
    clinic_name: str | None = None
    country: str | None = None
    city: str | None = None
    bio: str | None = None
    is_active: bool | None = None


class AdminDoctorStatusRequest(BaseModel):
    is_active: bool


class AdminActivityItem(BaseModel):
    type: str
    doctor_name: str
    patient_name: str
    timestamp: str
    scan_id: str | None = None


class AdminRecentDoctor(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    patient_count: int
    created_at: str


class AdminAnalyticsSummary(BaseModel):
    total_doctors: int
    active_doctors: int
    total_patients: int
    total_scans: int
    scans_today: int
    pending_reports: int
    sessions_this_month: int
    recent_activity: list[AdminActivityItem]
    recent_doctors: list[AdminRecentDoctor]
