import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.models.dataset_item import DatasetItemStatus, DatasetPoseType
from app.schemas.scan import RecomputeKeypointsRequest


class DatasetItemListItem(BaseModel):
    id: uuid.UUID
    pose_type: DatasetPoseType
    detector_model: str
    status: DatasetItemStatus
    original_filename: str | None
    image_url: str | None
    keypoint_count: int = 0
    keypoints_adjusted: bool = False
    created_at: datetime


class DatasetItemListResponse(BaseModel):
    items: list[DatasetItemListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class DatasetItemDetailResponse(BaseModel):
    id: uuid.UUID
    pose_type: DatasetPoseType
    detector_model: str
    status: DatasetItemStatus
    original_filename: str | None
    image_url: str | None
    keypoints: dict | None = None
    keypoints_adjusted: bool = False
    inference_error: str | None
    created_at: datetime
    updated_at: datetime


class DatasetItemCreateResponse(BaseModel):
    items: list[DatasetItemDetailResponse]
    created_count: int


class DatasetRecomputeRequest(RecomputeKeypointsRequest):
    pass


class DatasetResetKeypointsRequest(BaseModel):
    note: str | None = None


ManualLabelValue = Literal["yes", "no", "na"]


class DatasetManualLabelsRequest(BaseModel):
    """Manual clinical labels for dataset ground-truth annotation."""

    thoracic_kyphosis: ManualLabelValue | None = None
    lumbar_lordosis: ManualLabelValue | None = None
    pelvic_tilt_sagittal: ManualLabelValue | None = None
    pelvic_obliquity: ManualLabelValue | None = None
    knee_flexion_left: ManualLabelValue | None = None
    knee_flexion_right: ManualLabelValue | None = None
    hka_angle_left: ManualLabelValue | None = None
    hka_angle_right: ManualLabelValue | None = None
    forward_head_posture: ManualLabelValue | None = None
    shoulder_height_asymmetry: ManualLabelValue | None = None
    jaw_deviation: ManualLabelValue | None = None
    spine_drift: ManualLabelValue | None = None
    scapula_asymmetry: ManualLabelValue | None = None
    vertebral_rotation: ManualLabelValue | None = None
    adams_rib_hump: ManualLabelValue | None = None
