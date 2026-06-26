import os

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.doctor import Doctor
from app.schemas.auth import (
    AuthResponse,
    ChangePasswordRequest,
    DoctorRegisterRequest,
    DoctorResponse,
    DoctorUpdateRequest,
    ForgotPasswordRequest,
    MessageResponse,
)
from app.services import auth_service
from app.utils.dependencies import get_current_doctor

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: DoctorRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    return await auth_service.register_doctor(db, payload)


@router.post("/login", response_model=AuthResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    return await auth_service.login_doctor(db, form_data.username, form_data.password)


@router.get("/me", response_model=DoctorResponse)
async def get_me(current_doctor: Doctor = Depends(get_current_doctor)) -> DoctorResponse:
    return DoctorResponse.model_validate(current_doctor)


@router.put("/me", response_model=DoctorResponse)
async def update_me(
    payload: DoctorUpdateRequest,
    current_doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> DoctorResponse:
    return await auth_service.update_doctor_profile(db, current_doctor, payload)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: ChangePasswordRequest,
    current_doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> None:
    await auth_service.change_doctor_password(db, current_doctor, payload)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await auth_service.request_password_reset(db, payload.email)
    return MessageResponse(message="If that email exists, a reset link has been sent.")
