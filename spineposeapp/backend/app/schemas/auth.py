import re
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.patient import Gender, RiskLevel


class DoctorRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    specialty: str | None = None
    license_number: str | None = None
    clinic_name: str | None = None
    country: str | None = None
    city: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit")
        return value


class DoctorUpdateRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    specialty: str | None = None
    license_number: str | None = None
    clinic_name: str | None = None
    country: str | None = None
    city: str | None = None
    bio: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit")
        return value


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class DoctorResponse(BaseModel):
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
    created_at: datetime
    updated_at: datetime


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    doctor: DoctorResponse


class MessageResponse(BaseModel):
    message: str
