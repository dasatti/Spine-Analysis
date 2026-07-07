import logging
import secrets
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.doctor import Doctor
from app.schemas.auth import (
    AuthResponse,
    ChangePasswordRequest,
    DoctorRegisterRequest,
    DoctorResponse,
    DoctorUpdateRequest,
)
from app.utils.dependencies import create_access_token, hash_password, verify_password
from app.utils.exceptions import conflict, unauthorized

logger = logging.getLogger(__name__)


async def register_doctor(db: AsyncSession, payload: DoctorRegisterRequest) -> AuthResponse:
    existing = await db.execute(select(Doctor).where(Doctor.email == payload.email))
    if existing.scalar_one_or_none():
        raise conflict("EMAIL_EXISTS", "A doctor with this email already exists")

    doctor = Doctor(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        specialty=payload.specialty,
        license_number=payload.license_number,
        clinic_name=payload.clinic_name,
        country=payload.country,
        city=payload.city,
    )
    db.add(doctor)
    await db.commit()
    await db.refresh(doctor)
    token = create_access_token(doctor)
    return AuthResponse(
        access_token=token,
        doctor=DoctorResponse.model_validate(doctor),
    )


async def login_doctor(db: AsyncSession, email: str, password: str) -> AuthResponse:
    result = await db.execute(select(Doctor).where(Doctor.email == email))
    doctor = result.scalar_one_or_none()
    if doctor is None or not verify_password(password, doctor.hashed_password):
        raise unauthorized()
    if not doctor.is_active:
        from app.utils.exceptions import forbidden

        raise forbidden()
    token = create_access_token(doctor)
    return AuthResponse(
        access_token=token,
        doctor=DoctorResponse.model_validate(doctor),
    )


async def update_doctor_profile(
    db: AsyncSession, doctor: Doctor, payload: DoctorUpdateRequest
) -> DoctorResponse:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(doctor, field, value)
    await db.commit()
    await db.refresh(doctor)
    return DoctorResponse.model_validate(doctor)


async def change_doctor_password(
    db: AsyncSession, doctor: Doctor, payload: ChangePasswordRequest
) -> None:
    if not verify_password(payload.current_password, doctor.hashed_password):
        raise unauthorized("Current password is incorrect")
    doctor.hashed_password = hash_password(payload.new_password)
    await db.commit()


async def request_password_reset(db: AsyncSession, email: str) -> None:
    result = await db.execute(select(Doctor).where(Doctor.email == email))
    doctor = result.scalar_one_or_none()
    if doctor:
        token = secrets.token_urlsafe(32)
        logger.info("Password reset token for %s: %s", email, token)
