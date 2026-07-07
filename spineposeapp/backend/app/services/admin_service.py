import math
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.doctor import Doctor
from app.models.patient import Patient, RiskLevel
from app.models.scan import Scan, ScanStatus
from app.schemas.admin import (
    AdminAnalyticsSummary,
    AdminDoctorDetailResponse,
    AdminDoctorListItem,
    AdminDoctorListResponse,
    AdminDoctorUpdateRequest,
)
from app.utils.exceptions import bad_request, not_found


async def _doctor_counts(db: AsyncSession, doctor_id: uuid.UUID) -> tuple[int, int]:
    patient_count = (
        await db.execute(
            select(func.count())
            .select_from(Patient)
            .where(Patient.doctor_id == doctor_id, Patient.is_active.is_(True))
        )
    ).scalar_one()
    scan_count = (
        await db.execute(
            select(func.count())
            .select_from(Scan)
            .join(Patient, Scan.patient_id == Patient.id)
            .where(Patient.doctor_id == doctor_id)
        )
    ).scalar_one()
    return patient_count, scan_count


async def get_admin_analytics_summary(db: AsyncSession) -> AdminAnalyticsSummary:
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_doctors = (
        await db.execute(select(func.count()).select_from(Doctor))
    ).scalar_one()
    active_doctors = (
        await db.execute(
            select(func.count()).select_from(Doctor).where(Doctor.is_active.is_(True))
        )
    ).scalar_one()
    total_patients = (
        await db.execute(
            select(func.count())
            .select_from(Patient)
            .where(Patient.is_active.is_(True))
        )
    ).scalar_one()
    total_scans = (
        await db.execute(select(func.count()).select_from(Scan))
    ).scalar_one()
    scans_today = (
        await db.execute(
            select(func.count()).select_from(Scan).where(Scan.created_at >= today_start)
        )
    ).scalar_one()
    pending_reports = (
        await db.execute(
            select(func.count())
            .select_from(Scan)
            .where(
                Scan.status == ScanStatus.completed,
                Scan.overall_risk.in_([RiskLevel.monitor, RiskLevel.elevated]),
            )
        )
    ).scalar_one()
    sessions_this_month = (
        await db.execute(
            select(func.count()).select_from(Scan).where(Scan.created_at >= month_start)
        )
    ).scalar_one()

    recent_scans = await db.execute(
        select(Scan, Patient, Doctor)
        .select_from(Scan)
        .join(Patient, Scan.patient_id == Patient.id)
        .join(Doctor, Patient.doctor_id == Doctor.id)
        .where(Scan.status == ScanStatus.completed)
        .order_by(Scan.completed_at.desc())
        .limit(10)
    )
    recent_activity = [
        {
            "type": "scan_completed",
            "doctor_name": f"{doctor.first_name} {doctor.last_name}",
            "patient_name": f"{patient.first_name} {patient.last_name}",
            "timestamp": (
                scan.completed_at.isoformat()
                if scan.completed_at
                else scan.created_at.isoformat()
            ),
            "scan_id": str(scan.id),
        }
        for scan, patient, doctor in recent_scans.all()
    ]

    recent_doctors_result = await db.execute(
        select(Doctor).order_by(Doctor.created_at.desc()).limit(5)
    )
    recent_doctors = []
    for doctor in recent_doctors_result.scalars().all():
        patient_count, _ = await _doctor_counts(db, doctor.id)
        recent_doctors.append(
            {
                "id": str(doctor.id),
                "first_name": doctor.first_name,
                "last_name": doctor.last_name,
                "email": doctor.email,
                "patient_count": patient_count,
                "created_at": doctor.created_at.isoformat(),
            }
        )

    return AdminAnalyticsSummary(
        total_doctors=total_doctors,
        active_doctors=active_doctors,
        total_patients=total_patients,
        total_scans=total_scans,
        scans_today=scans_today,
        pending_reports=pending_reports,
        sessions_this_month=sessions_this_month,
        recent_activity=recent_activity,
        recent_doctors=recent_doctors,
    )


async def list_doctors(
    db: AsyncSession,
    page: int,
    page_size: int,
    search: str | None,
    is_active: bool | None,
) -> AdminDoctorListResponse:
    query = select(Doctor)
    count_query = select(func.count()).select_from(Doctor)

    if search:
        term = search.strip()
        pattern = f"%{term}%"
        filter_clause = or_(
            Doctor.first_name.ilike(pattern),
            Doctor.last_name.ilike(pattern),
            Doctor.email.ilike(pattern),
            func.concat(Doctor.first_name, " ", Doctor.last_name).ilike(pattern),
        )
        query = query.where(filter_clause)
        count_query = count_query.where(filter_clause)

    if is_active is not None:
        query = query.where(Doctor.is_active.is_(is_active))
        count_query = count_query.where(Doctor.is_active.is_(is_active))

    total = (await db.execute(count_query)).scalar_one()
    total_pages = max(1, math.ceil(total / page_size)) if total else 1

    result = await db.execute(
        query.order_by(Doctor.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = []
    for doctor in result.scalars().all():
        patient_count, scan_count = await _doctor_counts(db, doctor.id)
        item = AdminDoctorListItem.model_validate(doctor)
        item.patient_count = patient_count
        item.scan_count = scan_count
        items.append(item)

    return AdminDoctorListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


async def get_doctor_detail(db: AsyncSession, doctor_id: uuid.UUID) -> AdminDoctorDetailResponse:
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    if doctor is None:
        raise not_found("Doctor not found")
    patient_count, scan_count = await _doctor_counts(db, doctor.id)
    detail = AdminDoctorDetailResponse.model_validate(doctor)
    detail.patient_count = patient_count
    detail.scan_count = scan_count
    return detail


async def update_doctor(
    db: AsyncSession,
    admin: Doctor,
    doctor_id: uuid.UUID,
    payload: AdminDoctorUpdateRequest,
) -> AdminDoctorDetailResponse:
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    if doctor is None:
        raise not_found("Doctor not found")

    updates = payload.model_dump(exclude_unset=True)
    if doctor.id == admin.id and updates.get("is_active") is False:
        raise bad_request("You cannot deactivate your own account")

    for field, value in updates.items():
        setattr(doctor, field, value)

    await db.commit()
    await db.refresh(doctor)
    return await get_doctor_detail(db, doctor.id)


async def update_doctor_status(
    db: AsyncSession,
    admin: Doctor,
    doctor_id: uuid.UUID,
    is_active: bool,
) -> AdminDoctorDetailResponse:
    if doctor_id == admin.id and not is_active:
        raise bad_request("You cannot deactivate your own account")
    return await update_doctor(
        db,
        admin,
        doctor_id,
        AdminDoctorUpdateRequest(is_active=is_active),
    )
