import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.doctor import Doctor
from app.models.patient import RiskLevel
from app.schemas.patient import (
    PatientCreateRequest,
    PatientDetailResponse,
    PatientListResponse,
    PatientUpdateRequest,
)
from app.schemas.scan import ScanListResponse
from app.services import patient_service, scan_service
from app.utils.dependencies import get_current_doctor

router = APIRouter()


@router.post("", response_model=PatientDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    payload: PatientCreateRequest,
    current_doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> PatientDetailResponse:
    return await patient_service.create_patient(db, current_doctor, payload)


@router.get("", response_model=PatientListResponse)
async def list_patients(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    risk_level: RiskLevel | None = None,
    sort_by: str = Query("created_at", pattern="^(last_name|created_at|last_scan_date)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> PatientListResponse:
    return await patient_service.list_patients(
        db,
        current_doctor,
        page,
        page_size,
        search,
        risk_level,
        sort_by,
        sort_order,
    )


@router.get("/{patient_id}", response_model=PatientDetailResponse)
async def get_patient(
    patient_id: uuid.UUID,
    current_doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> PatientDetailResponse:
    return await patient_service.get_patient(db, current_doctor, patient_id)


@router.put("/{patient_id}", response_model=PatientDetailResponse)
async def update_patient(
    patient_id: uuid.UUID,
    payload: PatientUpdateRequest,
    current_doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> PatientDetailResponse:
    return await patient_service.update_patient(db, current_doctor, patient_id, payload)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: uuid.UUID,
    current_doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> None:
    await patient_service.soft_delete_patient(db, current_doctor, patient_id)


@router.get("/{patient_id}/scans", response_model=ScanListResponse)
async def list_patient_scans(
    patient_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> ScanListResponse:
    await patient_service.get_patient(db, current_doctor, patient_id)
    return await scan_service.list_scans(
        db,
        current_doctor,
        page,
        page_size,
        patient_id,
        None,
        None,
        None,
        None,
    )
