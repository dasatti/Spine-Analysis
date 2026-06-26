import math
import uuid
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.doctor import Doctor
from app.models.patient import Patient, RiskLevel
from app.models.scan import Scan, ScanStatus
from app.schemas.patient import (
    PatientCreateRequest,
    PatientDetailResponse,
    PatientListItem,
    PatientListResponse,
    PatientUpdateRequest,
    ScanSummary,
)
from app.utils.exceptions import conflict, not_found


async def _scan_stats(db: AsyncSession, patient_id: uuid.UUID) -> tuple[int, datetime | None]:
    count_result = await db.execute(
        select(func.count()).select_from(Scan).where(Scan.patient_id == patient_id)
    )
    count = count_result.scalar_one()
    last_result = await db.execute(
        select(func.max(Scan.created_at)).where(Scan.patient_id == patient_id)
    )
    return count, last_result.scalar_one_or_none()


async def create_patient(
    db: AsyncSession, doctor: Doctor, payload: PatientCreateRequest
) -> PatientDetailResponse:
    if payload.medical_record_number:
        existing = await db.execute(
            select(Patient).where(
                Patient.doctor_id == doctor.id,
                Patient.medical_record_number == payload.medical_record_number,
            )
        )
        if existing.scalar_one_or_none():
            raise conflict("MRN_EXISTS", "Medical record number already exists for this doctor")

    patient = Patient(doctor_id=doctor.id, **payload.model_dump())
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return PatientDetailResponse.model_validate(patient)


async def list_patients(
    db: AsyncSession,
    doctor: Doctor,
    page: int,
    page_size: int,
    search: str | None,
    risk_level: RiskLevel | None,
    sort_by: str,
    sort_order: str,
) -> PatientListResponse:
    query = select(Patient).where(Patient.doctor_id == doctor.id, Patient.is_active.is_(True))
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                Patient.first_name.ilike(pattern),
                Patient.last_name.ilike(pattern),
                Patient.medical_record_number.ilike(pattern),
            )
        )
    if risk_level:
        query = query.where(Patient.risk_level == risk_level)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    sort_map = {
        "last_name": Patient.last_name,
        "created_at": Patient.created_at,
        "last_scan_date": Patient.created_at,
    }
    sort_col = sort_map.get(sort_by, Patient.created_at)
    query = query.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    patients = result.scalars().all()

    items: list[PatientListItem] = []
    for patient in patients:
        scan_count, last_scan_at = await _scan_stats(db, patient.id)
        item = PatientListItem.model_validate(patient)
        item.scan_count = scan_count
        item.last_scan_at = last_scan_at
        items.append(item)

    pages = math.ceil(total / page_size) if total else 0
    return PatientListResponse(
        items=items, total=total, page=page, page_size=page_size, pages=pages
    )


async def get_patient(
    db: AsyncSession, doctor: Doctor, patient_id: uuid.UUID
) -> PatientDetailResponse:
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.doctor_id == doctor.id,
            Patient.is_active.is_(True),
        )
    )
    patient = result.scalar_one_or_none()
    if patient is None:
        raise not_found("Patient not found")

    scan_count, last_scan_at = await _scan_stats(db, patient.id)
    scans_result = await db.execute(
        select(Scan)
        .where(Scan.patient_id == patient.id)
        .order_by(Scan.created_at.desc())
        .limit(5)
    )
    recent_scans = []
    for scan in scans_result.scalars().all():
        metrics_count = len(scan.metrics_json or {}) if scan.metrics_json else 0
        recent_scans.append(
            ScanSummary(
                id=scan.id,
                status=scan.status,
                created_at=scan.created_at,
                detector_model=scan.detector_model,
                overall_risk=scan.overall_risk,
                metrics_count=metrics_count,
            )
        )

    detail = PatientDetailResponse.model_validate(patient)
    detail.scan_count = scan_count
    detail.last_scan_at = last_scan_at
    detail.recent_scans = recent_scans
    return detail


async def update_patient(
    db: AsyncSession,
    doctor: Doctor,
    patient_id: uuid.UUID,
    payload: PatientUpdateRequest,
) -> PatientDetailResponse:
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.doctor_id == doctor.id,
            Patient.is_active.is_(True),
        )
    )
    patient = result.scalar_one_or_none()
    if patient is None:
        raise not_found("Patient not found")

    updates = payload.model_dump(exclude_unset=True)
    if "medical_record_number" in updates and updates["medical_record_number"]:
        existing = await db.execute(
            select(Patient).where(
                Patient.doctor_id == doctor.id,
                Patient.medical_record_number == updates["medical_record_number"],
                Patient.id != patient.id,
            )
        )
        if existing.scalar_one_or_none():
            raise conflict("MRN_EXISTS", "Medical record number already exists for this doctor")

    for field, value in updates.items():
        setattr(patient, field, value)
    await db.commit()
    await db.refresh(patient)
    return await get_patient(db, doctor, patient.id)


async def soft_delete_patient(
    db: AsyncSession, doctor: Doctor, patient_id: uuid.UUID
) -> None:
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.doctor_id == doctor.id,
            Patient.is_active.is_(True),
        )
    )
    patient = result.scalar_one_or_none()
    if patient is None:
        raise not_found("Patient not found")
    patient.is_active = False
    await db.commit()
