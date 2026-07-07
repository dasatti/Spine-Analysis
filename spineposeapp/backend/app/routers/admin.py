import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.dataset_item import DatasetItemStatus, DatasetPoseType
from app.models.doctor import Doctor
from app.schemas.admin import (
    AdminAnalyticsSummary,
    AdminDoctorDetailResponse,
    AdminDoctorListResponse,
    AdminDoctorStatusRequest,
    AdminDoctorUpdateRequest,
)
from app.schemas.dataset import (
    DatasetItemCreateResponse,
    DatasetItemDetailResponse,
    DatasetItemListResponse,
    DatasetManualLabelsRequest,
    DatasetRecomputeRequest,
    DatasetResetKeypointsRequest,
    ResearchDatasetCreateRequest,
    ResearchDatasetListResponse,
    ResearchDatasetResponse,
    ResearchDatasetUpdateRequest,
)
from app.services import admin_service, dataset_service, research_dataset_service
from app.services import dataset_export
from app.utils.dependencies import get_current_admin
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


async def _read_upload(upload: UploadFile) -> tuple[bytes, str | None, str | None]:
    content_type = (upload.content_type or "").lower().split(";")[0].strip()
    filename = upload.filename or ""
    ext = f".{filename.rsplit('.', 1)[-1].lower()}" if "." in filename else ""

    type_ok = content_type in ALLOWED_FRAME_TYPES or content_type in ("", "application/octet-stream")
    ext_ok = ext in ALLOWED_FRAME_EXTENSIONS
    if not type_ok and not ext_ok:
        raise AppError(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "INVALID_FRAME_FORMAT",
            "Images must be PNG, JPEG, or TIFF",
        )
    if content_type in ("", "application/octet-stream") and not ext_ok:
        raise AppError(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "INVALID_FRAME_FORMAT",
            "Images must be PNG, JPEG, or TIFF",
        )
    return await upload.read(), upload.content_type, upload.filename


@router.get("/analytics/summary", response_model=AdminAnalyticsSummary)
async def get_analytics_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Doctor, Depends(get_current_admin)],
):
    return await admin_service.get_admin_analytics_summary(db)


@router.get("/doctors", response_model=AdminDoctorListResponse)
async def list_doctors(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Doctor, Depends(get_current_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    is_active: bool | None = None,
):
    return await admin_service.list_doctors(db, page, page_size, search, is_active)


@router.get("/doctors/{doctor_id}", response_model=AdminDoctorDetailResponse)
async def get_doctor(
    doctor_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Doctor, Depends(get_current_admin)],
):
    return await admin_service.get_doctor_detail(db, doctor_id)


@router.put("/doctors/{doctor_id}", response_model=AdminDoctorDetailResponse)
async def update_doctor(
    doctor_id: uuid.UUID,
    payload: AdminDoctorUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[Doctor, Depends(get_current_admin)],
):
    return await admin_service.update_doctor(db, admin, doctor_id, payload)


@router.patch("/doctors/{doctor_id}/status", response_model=AdminDoctorDetailResponse)
async def update_doctor_status(
    doctor_id: uuid.UUID,
    payload: AdminDoctorStatusRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[Doctor, Depends(get_current_admin)],
):
    return await admin_service.update_doctor_status(
        db, admin, doctor_id, payload.is_active
    )


@router.get("/datasets", response_model=ResearchDatasetListResponse)
async def list_research_datasets(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Doctor, Depends(get_current_admin)],
):
    return await research_dataset_service.list_research_datasets(db)


@router.post("/datasets", response_model=ResearchDatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_research_dataset(
    payload: ResearchDatasetCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[Doctor, Depends(get_current_admin)],
):
    return await research_dataset_service.create_research_dataset(db, admin, payload)


@router.put("/datasets/{dataset_id}", response_model=ResearchDatasetResponse)
async def update_research_dataset(
    dataset_id: uuid.UUID,
    payload: ResearchDatasetUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Doctor, Depends(get_current_admin)],
):
    return await research_dataset_service.update_research_dataset(db, dataset_id, payload)


@router.delete("/datasets/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_research_dataset(
    dataset_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Doctor, Depends(get_current_admin)],
):
    await research_dataset_service.delete_research_dataset(db, dataset_id)


@router.get("/dataset-items", response_model=DatasetItemListResponse)
async def list_dataset_items(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Doctor, Depends(get_current_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    dataset_id: uuid.UUID | None = None,
    pose_type: DatasetPoseType | None = None,
    detector_model: str | None = None,
    status: DatasetItemStatus | None = None,
):
    return await dataset_service.list_dataset_items(
        db, page, page_size, dataset_id, pose_type, detector_model, status
    )


@router.get("/dataset-items/export")
async def export_dataset_items(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Doctor, Depends(get_current_admin)],
    pose_type: DatasetPoseType | None = None,
    detector_model: str | None = None,
    status: DatasetItemStatus | None = None,
    dataset_id: uuid.UUID | None = None,
):
    csv_content, filename = await dataset_export.export_dataset_items_csv(
        db, dataset_id, pose_type, detector_model, status
    )
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/dataset-items", response_model=DatasetItemCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset_items(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[Doctor, Depends(get_current_admin)],
    dataset_id: uuid.UUID = Form(...),
    pose_type: DatasetPoseType = Form(...),
    detector_model: str = Form(...),
    images: list[UploadFile] = File(...),
):
    if not images:
        raise AppError(status.HTTP_422_UNPROCESSABLE_ENTITY, "NO_IMAGES", "At least one image is required")
    uploads = [await _read_upload(image) for image in images]
    return await dataset_service.create_dataset_items(
        db, admin, uploads, dataset_id, pose_type, detector_model
    )


@router.get("/dataset-items/{item_id}", response_model=DatasetItemDetailResponse)
async def get_dataset_item(
    item_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Doctor, Depends(get_current_admin)],
):
    return await dataset_service.get_dataset_item(db, item_id)


@router.post("/dataset-items/{item_id}/recompute", response_model=DatasetItemDetailResponse)
async def recompute_dataset_item(
    item_id: uuid.UUID,
    payload: DatasetRecomputeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[Doctor, Depends(get_current_admin)],
):
    return await dataset_service.recompute_dataset_item(db, admin, item_id, payload)


@router.put("/dataset-items/{item_id}/manual-labels", response_model=DatasetItemDetailResponse)
async def save_dataset_manual_labels(
    item_id: uuid.UUID,
    payload: DatasetManualLabelsRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[Doctor, Depends(get_current_admin)],
):
    return await dataset_service.save_manual_labels(db, admin, item_id, payload)


@router.post("/dataset-items/{item_id}/reset-keypoints", response_model=DatasetItemDetailResponse)
async def reset_dataset_item_keypoints(
    item_id: uuid.UUID,
    payload: DatasetResetKeypointsRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[Doctor, Depends(get_current_admin)],
):
    return await dataset_service.reset_dataset_item_keypoints(db, admin, item_id, payload.note)
