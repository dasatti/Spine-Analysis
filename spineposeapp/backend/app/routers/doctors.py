import os
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.doctor import Doctor
from app.pipeline.loader import (
    DETECTOR_LABELS,
    SELECTABLE_DETECTORS,
    detector_backend_ready,
    effective_detector_model,
)
from app.services import scan_service
from app.utils.dependencies import get_current_doctor
from app.utils.exceptions import bad_request

router = APIRouter()


class DetectorOption(BaseModel):
    id: str
    label: str
    ready: bool


class SettingsResponse(BaseModel):
    detector_model: str
    preferred_detector_model: str | None
    default_detector_model: str
    available_detectors: list[DetectorOption]
    keypoint_confidence_threshold: float
    model_weights_loaded: bool


class UpdateDetectorSettingsRequest(BaseModel):
    detector_model: Literal["spinepose_v2", "yolo_v8"] = Field(
        description="Pose detector to use for new scans"
    )


def _build_settings_response(doctor: Doctor) -> SettingsResponse:
    effective = effective_detector_model(doctor.preferred_detector_model)
    custom_weights = bool(
        settings.model_weights_path and os.path.exists(settings.model_weights_path)
    )
    if effective == "spinepose_v2":
        weights_loaded = custom_weights or detector_backend_ready("spinepose_v2")
    else:
        weights_loaded = detector_backend_ready("yolo_v8")

    available = [
        DetectorOption(
            id=model_id,
            label=DETECTOR_LABELS[model_id],
            ready=detector_backend_ready(model_id),
        )
        for model_id in SELECTABLE_DETECTORS
    ]
    return SettingsResponse(
        detector_model=effective,
        preferred_detector_model=doctor.preferred_detector_model,
        default_detector_model=settings.detector_model,
        available_detectors=available,
        keypoint_confidence_threshold=settings.keypoint_confidence_threshold,
        model_weights_loaded=weights_loaded,
    )


@router.get("/settings", response_model=SettingsResponse)
async def get_settings(
    current_doctor: Doctor = Depends(get_current_doctor),
) -> SettingsResponse:
    return _build_settings_response(current_doctor)


@router.put("/settings/detector", response_model=SettingsResponse)
async def update_detector_settings(
    payload: UpdateDetectorSettingsRequest,
    current_doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> SettingsResponse:
    if not detector_backend_ready(payload.detector_model):
        raise bad_request(
            f"Detector '{payload.detector_model}' is not available on this server"
        )

    current_doctor.preferred_detector_model = payload.detector_model
    await db.commit()
    await db.refresh(current_doctor)
    return _build_settings_response(current_doctor)


@router.get("/dashboard/summary")
async def dashboard_summary(
    current_doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await scan_service.get_dashboard_summary(db, current_doctor)
