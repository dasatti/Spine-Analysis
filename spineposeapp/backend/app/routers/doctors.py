import os

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.doctor import Doctor
from app.services import scan_service
from app.utils.dependencies import get_current_doctor

router = APIRouter()


class SettingsResponse(BaseModel):
    detector_model: str
    keypoint_confidence_threshold: float
    model_weights_loaded: bool


@router.get("/settings", response_model=SettingsResponse)
async def get_settings(
    current_doctor: Doctor = Depends(get_current_doctor),
) -> SettingsResponse:
    weights_loaded = bool(
        settings.model_weights_path and os.path.exists(settings.model_weights_path)
    )
    return SettingsResponse(
        detector_model=settings.detector_model,
        keypoint_confidence_threshold=settings.keypoint_confidence_threshold,
        model_weights_loaded=weights_loaded,
    )


@router.get("/dashboard/summary")
async def dashboard_summary(
    current_doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await scan_service.get_dashboard_summary(db, current_doctor)
