import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.doctor import Doctor
from app.models.scan import ScanStatus
from app.schemas.scan import ScanCreateResponse, ScanDetailResponse, ScanListResponse, ScanStatusResponse
from app.schemas.scan import RecomputeKeypointsRequest, ResetKeypointsRequest
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


async def _read_optional_frame(upload: UploadFile | None) -> FrameUpload | None:
    if upload is None or not upload.filename:
        return None
    return await _read_frame(upload)


@router.post("", response_model=ScanCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_scan(
    patient_id: uuid.UUID = Form(...),
    patient_height_cm: float = Form(...),
    patient_weight_kg: float = Form(...),
    capture_device: str | None = Form(None),
    camera_height_cm: float | None = Form(None),
    camera_distance_cm: float | None = Form(None),
    frame_front: UploadFile | None = File(None),
    frame_side: UploadFile | None = File(None),
    frame_back: UploadFile | None = File(None),
    frame_upper_body: UploadFile | None = File(None),
    frame_adams: UploadFile | None = File(None),
    frame_face: UploadFile | None = File(None),
    current_doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> ScanCreateResponse:
    frame_inputs = {
        "front": frame_front,
        "side": frame_side,
        "back": frame_back,
        "upper_body": frame_upper_body,
        "adams": frame_adams,
        "face": frame_face,
    }
    frames: dict[str, FrameUpload] = {}
    for view, upload in frame_inputs.items():
        frame = await _read_optional_frame(upload)
        if frame is not None:
            frames[view] = frame

    if not frames:
        raise AppError(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "NO_FRAMES",
            "At least one capture view is required",
        )

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


@router.post("/{scan_id}/recompute", response_model=ScanDetailResponse)
async def recompute_scan_keypoints(
    scan_id: uuid.UUID,
    payload: RecomputeKeypointsRequest,
    current_doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> ScanDetailResponse:
    return await scan_service.recompute_scan_keypoints(db, current_doctor, scan_id, payload)


@router.post("/{scan_id}/reset-keypoints", response_model=ScanDetailResponse)
async def reset_scan_keypoints(
    scan_id: uuid.UUID,
    payload: ResetKeypointsRequest,
    current_doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> ScanDetailResponse:
    return await scan_service.reset_scan_keypoints(db, current_doctor, scan_id, payload)


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan(
    scan_id: uuid.UUID,
    current_doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> None:
    await scan_service.delete_scan(db, current_doctor, scan_id)
