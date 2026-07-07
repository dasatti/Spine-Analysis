"""CSV export for dataset items with keypoints, computed metrics, and manual labels."""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.constants.manual_labels import MANUAL_LABEL_KEYS
from app.models.dataset_item import DatasetItem, DatasetItemStatus, DatasetPoseType
from app.services.dataset_service import _normalize_detector
from app.services.dataset_metrics import compute_dataset_metrics, landmarks_for_pose

BASE_COLUMNS = [
    "item_id",
    "dataset_id",
    "dataset_name",
    "filename",
    "pose_type",
    "detector_model",
    "status",
    "keypoints_adjusted",
    "created_at",
]

COMPUTED_METRIC_COLUMNS: list[tuple[str, str]] = [
    ("spinal_curves", "thoracic_kyphosis_deg"),
    ("spinal_curves", "lumbar_lordosis_deg"),
    ("pelvis_lower_body", "pelvic_tilt_sagittal_deg"),
    ("pelvis_lower_body", "pelvic_obliquity_mm"),
    ("pelvis_lower_body", "knee_flexion_left_deg"),
    ("pelvis_lower_body", "knee_flexion_right_deg"),
    ("pelvis_lower_body", "hka_angle_left_deg"),
    ("pelvis_lower_body", "hka_angle_right_deg"),
    ("head_shoulders", "forward_head_posture_mm"),
    ("head_shoulders", "shoulder_height_asymmetry_mm"),
    ("head_shoulders", "jaw_deviation_mm"),
    ("spine_back", "spine_drift_mm"),
    ("spine_back", "scapula_asymmetry_index"),
    ("spine_back", "vertebral_rotation_index"),
    ("spine_back", "adams_rib_hump_present"),
]

MANUAL_LABEL_COLUMNS = sorted(MANUAL_LABEL_KEYS)


def _landmarks_for_pose(keypoints_json: dict | None, pose_type: str) -> list[dict]:
    return landmarks_for_pose(keypoints_json, pose_type)


def _collect_keypoint_names(items: list[DatasetItem]) -> list[str]:
    names: set[str] = set()
    for item in items:
        for kp in _landmarks_for_pose(item.keypoints_json, item.pose_type.value):
            name = kp.get("name")
            if name:
                names.add(name)
    return sorted(names)


def _keypoint_columns(names: list[str]) -> list[str]:
    columns: list[str] = []
    for name in names:
        columns.extend([f"{name}_x", f"{name}_y", f"{name}_confidence"])
    return columns


def _compute_metrics(frame_landmarks: list[dict], detector_model: str) -> dict | None:
    return compute_dataset_metrics(frame_landmarks, detector_model)


def _metric_cell(metrics: dict | None, section: str, key: str) -> str:
    if not metrics:
        return ""
    payload = (metrics.get(section) or {}).get(key)
    if not payload or payload.get("value") is None:
        return ""
    value = payload["value"]
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _landmark_map(landmarks: list[dict]) -> dict[str, dict]:
    return {kp["name"]: kp for kp in landmarks if kp.get("name")}


def _row_for_item(
    item: DatasetItem,
    keypoint_names: list[str],
    metrics: dict | None,
) -> dict[str, str]:
    audit = (item.keypoints_json or {}).get("audit") or {}
    manual_labels = (item.keypoints_json or {}).get("manual_labels") or {}
    landmarks = _landmark_map(_landmarks_for_pose(item.keypoints_json, item.pose_type.value))

    row: dict[str, str] = {
        "item_id": str(item.id),
        "dataset_id": str(item.dataset_id),
        "dataset_name": item.dataset.name if item.dataset else "",
        "filename": item.original_filename or "",
        "pose_type": item.pose_type.value,
        "detector_model": item.detector_model,
        "status": item.status.value,
        "keypoints_adjusted": "true" if audit.get("adjusted_at") else "false",
        "created_at": item.created_at.isoformat() if item.created_at else "",
    }

    for name in keypoint_names:
        kp = landmarks.get(name)
        row[f"{name}_x"] = "" if kp is None or kp.get("x") is None else str(kp["x"])
        row[f"{name}_y"] = "" if kp is None or kp.get("y") is None else str(kp["y"])
        row[f"{name}_confidence"] = (
            "" if kp is None or kp.get("confidence") is None else str(kp["confidence"])
        )

    for section, key in COMPUTED_METRIC_COLUMNS:
        row[key] = _metric_cell(metrics, section, key)

    for label_key in MANUAL_LABEL_COLUMNS:
        row[f"manual_{label_key}"] = str(manual_labels.get(label_key) or "")

    return row


async def _fetch_items(
    db: AsyncSession,
    dataset_id: uuid.UUID | None,
    pose_type: DatasetPoseType | None,
    detector_model: str | None,
    status: DatasetItemStatus | None,
) -> list[DatasetItem]:
    query = select(DatasetItem).options(selectinload(DatasetItem.dataset))
    if dataset_id is not None:
        query = query.where(DatasetItem.dataset_id == dataset_id)
    if pose_type is not None:
        query = query.where(DatasetItem.pose_type == pose_type)
    if detector_model:
        resolved = _normalize_detector(detector_model)
        query = query.where(DatasetItem.detector_model == resolved)
    if status is not None:
        query = query.where(DatasetItem.status == status)
    result = await db.execute(query.order_by(DatasetItem.created_at.desc()))
    return list(result.scalars().all())


def build_dataset_csv(items: list[DatasetItem]) -> str:
    keypoint_names = _collect_keypoint_names(items)
    headers = (
        BASE_COLUMNS
        + _keypoint_columns(keypoint_names)
        + [key for _, key in COMPUTED_METRIC_COLUMNS]
        + [f"manual_{key}" for key in MANUAL_LABEL_COLUMNS]
    )

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()

    for item in items:
        metrics = None
        if item.status == DatasetItemStatus.ready:
            frame_landmarks = _landmarks_for_pose(item.keypoints_json, item.pose_type.value)
            metrics = _compute_metrics(frame_landmarks, item.detector_model)
        writer.writerow(_row_for_item(item, keypoint_names, metrics))

    return buffer.getvalue()


async def export_dataset_items_csv(
    db: AsyncSession,
    dataset_id: uuid.UUID | None,
    pose_type: DatasetPoseType | None,
    detector_model: str | None,
    status: DatasetItemStatus | None,
) -> tuple[str, str]:
    items = await _fetch_items(db, dataset_id, pose_type, detector_model, status)
    csv_content = build_dataset_csv(items)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"dataset_export_{timestamp}.csv"
    return csv_content, filename
