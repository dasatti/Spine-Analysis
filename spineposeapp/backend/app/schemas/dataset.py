import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

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
