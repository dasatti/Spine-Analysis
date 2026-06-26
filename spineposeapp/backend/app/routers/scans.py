import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.doctor import Doctor
from app.models.scan import ScanStatus
from app.schemas.scan import ScanCreateResponse, ScanDetailResponse, ScanListResponse, ScanStatusResponse
from app.services import scan_service
from app.services.scan_service import FrameUpload
from app.utils.dependencies import get_current_doctor
from app.utils.exceptions import AppError

router = APIRouter()

ALLOWED_FRAME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/tiff",
    "image/tif",
}
ALLOWED_FRAME_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}


async def _read_frame(upload: UploadFile) -> FrameUpload:
    content_type = (upload.content_type or "").lower().split(";")[0].strip()
    filename = upload.filename or ""
    ext = f".{filename.rsplit('.', 1)[-1].lower()}" if "." in filename else ""

    type_ok = content_type in ALLOWED_FRAME_TYPES or content_type in ("", "application/octet-stream")
    ext_ok = ext in ALLOWED_FRAME_EXTENSIONS
    if not type_ok and not ext_ok:
        raise AppError(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "INVALID_FRAME_FORMAT",
            "Frames must be PNG, JPEG, or TIFF",
        )
    if content_type in ("", "application/octet-stream") and not ext_ok:
        raise AppError(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "INVALID_FRAME_FORMAT",
            "Frames must be PNG, JPEG, or TIFF",
        )

    return FrameUpload(
        data=await upload.read(),
        content_type=upload.content_type,
        filename=upload.filename,
    )


@router.post("", response_model=ScanCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_scan(
    patient_id: uuid.UUID = Form(...),
    patient_height_cm: float = Form(...),
    patient_weight_kg: float = Form(...),
    capture_device: str | None = Form(None),
    camera_height_cm: float | None = Form(None),
    camera_distance_cm: float | None = Form(None),
    frame_front: UploadFile = File(...),
    frame_side: UploadFile = File(...),
    frame_back: UploadFile = File(...),
    frame_adams: UploadFile = File(...),
    frame_face: UploadFile | None = File(None),
    current_doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> ScanCreateResponse:
    frames = {
        "front": await _read_frame(frame_front),
        "side": await _read_frame(frame_side),
        "back": await _read_frame(frame_back),
        "adams": await _read_frame(frame_adams),
    }
    if frame_face is not None:
        frames["face"] = await _read_frame(frame_face)

    return await scan_service.create_scan(
        db,
        current_doctor,
        patient_id,
        capture_device,
        camera_height_cm,
        camera_distance_cm,
        patient_height_cm,
        patient_weight_kg,
        frames,
    )


@router.get("", response_model=ScanListResponse)
async def list_scans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    patient_id: uuid.UUID | None = None,
    status_filter: ScanStatus | None = Query(None, alias="status"),
    detector_model: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    current_doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> ScanListResponse:
    return await scan_service.list_scans(
        db,
        current_doctor,
        page,
        page_size,
        patient_id,
        status_filter,
        detector_model,
        date_from,
        date_to,
    )


@router.get("/{scan_id}/status", response_model=ScanStatusResponse)
async def get_scan_status(
    scan_id: uuid.UUID,
    current_doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> ScanStatusResponse:
    return await scan_service.get_scan_status(db, current_doctor, scan_id)


@router.get("/{scan_id}", response_model=ScanDetailResponse)
async def get_scan(
    scan_id: uuid.UUID,
    current_doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> ScanDetailResponse:
    return await scan_service.get_scan_detail(db, current_doctor, scan_id)


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan(
    scan_id: uuid.UUID,
    current_doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> None:
    await scan_service.delete_scan(db, current_doctor, scan_id)
