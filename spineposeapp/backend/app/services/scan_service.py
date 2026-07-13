import math
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.doctor import Doctor
from app.pipeline.loader import effective_detector_model
from app.models.patient import Patient, RiskLevel
from app.models.scan import Scan, ScanStatus
from app.schemas.scan import (
    FrameUrls,
    PatientBrief,
    RecomputeKeypointsRequest,
    ResetKeypointsRequest,
    ScanCreateResponse,
    ScanDetailResponse,
    ScanListItem,
    ScanListResponse,
    ScanStatusResponse,
)
from app.services.recompute_service import recompute_scan_keypoints as run_recompute
from app.services.recompute_service import reset_scan_keypoints as run_reset
from app.services.storage_service import resolve_frame_format, storage_service
from app.utils.exceptions import bad_request, conflict, not_found


@dataclass
class FrameUpload:
    data: bytes
    content_type: str | None = None
    filename: str | None = None


async def _get_owned_patient(
    db: AsyncSession, doctor: Doctor, patient_id: uuid.UUID
) -> Patient:
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
    return patient


async def _get_owned_scan(db: AsyncSession, doctor: Doctor, scan_id: uuid.UUID) -> Scan:
    result = await db.execute(
        select(Scan)
        .join(Patient)
        .where(Scan.id == scan_id, Patient.doctor_id == doctor.id)
        .options(selectinload(Scan.patient))
    )
    scan = result.scalar_one_or_none()
    if scan is None:
        raise not_found("Scan not found")
    return scan


def _frame_urls(scan_id: uuid.UUID) -> FrameUrls:
    prefix = storage_service.scan_frames_prefix(str(scan_id))
    views = ["front", "side", "back", "upper_body", "adams", "face"]
    urls = {}
    for view in views:
        key = storage_service.find_frame_key(prefix, view)
        urls[view] = storage_service.presigned_url(key) if key else None
    return FrameUrls(**urls)


def _normalize_frame_landmarks(frame_landmarks: list) -> list[dict]:
    normalized: list[dict] = []
    for item in frame_landmarks:
        if hasattr(item, "model_dump"):
            entry = item.model_dump()
        elif isinstance(item, dict):
            entry = dict(item)
        else:
            continue
        if not entry.get("view"):
            entry["view"] = entry.get("source_view") or "front"
        normalized.append(entry)
    return normalized


def _scan_detail_response(scan: Scan) -> ScanDetailResponse:
    twin_url = None
    if scan.digital_twin_url:
        twin_url = storage_service.presigned_url(scan.digital_twin_url)
    audit = (scan.keypoints_json or {}).get("audit") or {}

    return ScanDetailResponse(
        id=scan.id,
        patient_id=scan.patient_id,
        patient=PatientBrief(
            first_name=scan.patient.first_name,
            last_name=scan.patient.last_name,
        ),
        status=scan.status,
        detector_model=scan.detector_model,
        capture_device=scan.capture_device,
        camera_height_cm=scan.camera_height_cm,
        camera_distance_cm=scan.camera_distance_cm,
        patient_height_cm=scan.patient_height_cm,
        patient_weight_kg=scan.patient_weight_kg,
        overall_risk=scan.overall_risk,
        digital_twin_url=twin_url,
        metrics=scan.metrics_json,
        keypoints=scan.keypoints_json,
        keypoints_adjusted=bool(audit.get("adjusted_at")),
        error_message=scan.error_message,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        created_at=scan.created_at,
        frame_urls=_frame_urls(scan.id),
    )


async def create_scan(
    db: AsyncSession,
    doctor: Doctor,
    patient_id: uuid.UUID,
    capture_device: str | None,
    camera_height_cm: float | None,
    camera_distance_cm: float | None,
    patient_height_cm: float,
    patient_weight_kg: float,
    frames: dict[str, FrameUpload],
) -> ScanCreateResponse:
    patient = await _get_owned_patient(db, doctor, patient_id)
    scan = Scan(
        patient_id=patient.id,
        doctor_id=doctor.id,
        status=ScanStatus.pending,
        capture_device=capture_device,
        camera_height_cm=camera_height_cm,
        camera_distance_cm=camera_distance_cm,
        patient_height_cm=patient_height_cm,
        patient_weight_kg=patient_weight_kg,
        detector_model=effective_detector_model(doctor.preferred_detector_model),
        progress_message="Queued for processing",
    )
    db.add(scan)
    await db.flush()

    prefix = storage_service.scan_frames_prefix(str(scan.id))
    for view, frame in frames.items():
        ext, media_type = resolve_frame_format(frame.content_type, frame.filename)
        key = f"{prefix}{view}.{ext}"
        storage_service.upload_bytes(key, frame.data, media_type)

    scan.raw_frames_prefix = prefix
    await db.commit()
    await db.refresh(scan)

    from app.workers.scan_tasks import process_scan

    process_scan.delay(str(scan.id))

    return ScanCreateResponse(
        id=scan.id,
        patient_id=scan.patient_id,
        status=scan.status,
        detector_model=scan.detector_model,
        created_at=scan.created_at,
    )


async def get_scan_status(
    db: AsyncSession, doctor: Doctor, scan_id: uuid.UUID
) -> ScanStatusResponse:
    scan = await _get_owned_scan(db, doctor, scan_id)
    return ScanStatusResponse(
        id=scan.id,
        status=scan.status,
        progress_message=scan.progress_message,
        detector_model=scan.detector_model,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
    )


async def get_scan_detail(
    db: AsyncSession, doctor: Doctor, scan_id: uuid.UUID
) -> ScanDetailResponse:
    scan = await _get_owned_scan(db, doctor, scan_id)
    return _scan_detail_response(scan)


async def recompute_scan_keypoints(
    db: AsyncSession,
    doctor: Doctor,
    scan_id: uuid.UUID,
    payload: RecomputeKeypointsRequest,
) -> ScanDetailResponse:
    scan = await _get_owned_scan(db, doctor, scan_id)
    if scan.status != ScanStatus.completed:
        raise conflict("SCAN_NOT_COMPLETED", "Keypoints can only be adjusted on completed scans")

    frame_landmarks = _normalize_frame_landmarks(payload.frame_landmarks)
    try:
        run_recompute(
            scan,
            scan.patient,
            frame_landmarks,
            doctor_id=doctor.id,
            preserve_manual_spine=payload.preserve_manual_spine,
            refresh_synthetics=payload.refresh_synthetics,
            views_refreshed=payload.views_refreshed,
            note=payload.note,
        )
    except ValueError as exc:
        raise bad_request(str(exc)) from exc

    await db.commit()
    await db.refresh(scan)
    return _scan_detail_response(scan)


async def reset_scan_keypoints(
    db: AsyncSession,
    doctor: Doctor,
    scan_id: uuid.UUID,
    payload: ResetKeypointsRequest,
) -> ScanDetailResponse:
    scan = await _get_owned_scan(db, doctor, scan_id)
    if scan.status != ScanStatus.completed:
        raise conflict("SCAN_NOT_COMPLETED", "Keypoints can only be reset on completed scans")

    try:
        run_reset(scan, scan.patient, doctor_id=doctor.id, note=payload.note)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc

    await db.commit()
    await db.refresh(scan)
    return _scan_detail_response(scan)


async def list_scans(
    db: AsyncSession,
    doctor: Doctor,
    page: int,
    page_size: int,
    patient_id: uuid.UUID | None,
    status: ScanStatus | None,
    detector_model: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
) -> ScanListResponse:
    query = (
        select(Scan, Patient)
        .join(Patient)
        .where(Patient.doctor_id == doctor.id)
    )
    if patient_id:
        query = query.where(Scan.patient_id == patient_id)
    if status:
        query = query.where(Scan.status == status)
    if detector_model:
        query = query.where(Scan.detector_model == detector_model)
    if date_from:
        query = query.where(Scan.created_at >= date_from)
    if date_to:
        query = query.where(Scan.created_at <= date_to)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    query = query.order_by(Scan.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rows = result.all()

    items = [
        ScanListItem(
            id=scan.id,
            patient_id=scan.patient_id,
            patient_name=f"{patient.first_name} {patient.last_name}",
            status=scan.status,
            detector_model=scan.detector_model,
            overall_risk=scan.overall_risk,
            created_at=scan.created_at,
            completed_at=scan.completed_at,
        )
        for scan, patient in rows
    ]
    pages = math.ceil(total / page_size) if total else 0
    return ScanListResponse(
        items=items, total=total, page=page, page_size=page_size, pages=pages
    )


async def delete_scan(db: AsyncSession, doctor: Doctor, scan_id: uuid.UUID) -> None:
    scan = await _get_owned_scan(db, doctor, scan_id)
    if scan.status == ScanStatus.processing:
        raise conflict("SCAN_PROCESSING", "Cannot delete scan while processing")
    prefix = f"scans/{scan.id}/"
    storage_service.delete_prefix(prefix)
    await db.delete(scan)
    await db.commit()


async def get_dashboard_summary(db: AsyncSession, doctor: Doctor) -> dict:
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_patients = (
        await db.execute(
            select(func.count())
            .select_from(Patient)
            .where(Patient.doctor_id == doctor.id, Patient.is_active.is_(True))
        )
    ).scalar_one()

    scans_today = (
        await db.execute(
            select(func.count())
            .select_from(Scan)
            .join(Patient)
            .where(
                Patient.doctor_id == doctor.id,
                Scan.created_at >= today_start,
            )
        )
    ).scalar_one()

    pending_reports = (
        await db.execute(
            select(func.count())
            .select_from(Scan)
            .join(Patient)
            .where(
                Patient.doctor_id == doctor.id,
                Scan.status == ScanStatus.completed,
                Scan.overall_risk.in_([RiskLevel.monitor, RiskLevel.elevated]),
            )
        )
    ).scalar_one()

    sessions_this_month = (
        await db.execute(
            select(func.count())
            .select_from(Scan)
            .join(Patient)
            .where(Patient.doctor_id == doctor.id, Scan.created_at >= month_start)
        )
    ).scalar_one()

    recent_scans = await db.execute(
        select(Scan, Patient)
        .join(Patient)
        .where(Patient.doctor_id == doctor.id, Scan.status == ScanStatus.completed)
        .order_by(Scan.completed_at.desc())
        .limit(5)
    )
    recent_activity = [
        {
            "type": "scan_completed",
            "patient_name": f"{patient.first_name} {patient.last_name}",
            "timestamp": scan.completed_at.isoformat() if scan.completed_at else scan.created_at.isoformat(),
            "scan_id": str(scan.id),
        }
        for scan, patient in recent_scans.all()
    ]

    recent_patients_result = await db.execute(
        select(Patient)
        .where(Patient.doctor_id == doctor.id, Patient.is_active.is_(True))
        .order_by(Patient.created_at.desc())
        .limit(5)
    )
    recent_patients = [
        {
            "id": str(p.id),
            "first_name": p.first_name,
            "last_name": p.last_name,
            "risk_level": p.risk_level.value,
            "created_at": p.created_at.isoformat(),
        }
        for p in recent_patients_result.scalars().all()
    ]

    return {
        "total_patients": total_patients,
        "scans_today": scans_today,
        "pending_reports": pending_reports,
        "sessions_this_month": sessions_this_month,
        "recent_activity": recent_activity,
        "recent_patients": recent_patients,
    }
