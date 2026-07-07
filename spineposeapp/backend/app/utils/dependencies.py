from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.doctor import Doctor, DoctorRole
from app.utils.exceptions import forbidden, unauthorized

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(doctor: Doctor) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(doctor.id), "role": doctor.role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


async def get_current_doctor(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Doctor:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        doctor_id = payload.get("sub")
        if doctor_id is None:
            raise unauthorized()
    except JWTError as exc:
        raise unauthorized() from exc

    result = await db.execute(select(Doctor).where(Doctor.id == UUID(doctor_id)))
    doctor = result.scalar_one_or_none()
    if doctor is None:
        raise unauthorized()
    if not doctor.is_active:
        raise forbidden()
    return doctor


async def get_current_admin(
    doctor: Annotated[Doctor, Depends(get_current_doctor)],
) -> Doctor:
    if doctor.role != DoctorRole.admin.value:
        raise forbidden("Admin access required")
    return doctor
