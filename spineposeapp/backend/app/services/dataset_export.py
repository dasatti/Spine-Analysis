"""CSV export for dataset items with keypoints, computed metrics, and manual labels."""

from __future__ import annotations

import csv
import io
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.manual_labels import MANUAL_LABEL_KEYS
from app.models.dataset_item import DatasetItem, DatasetItemStatus, DatasetPoseType
from app.pipeline.head_shoulder_metrics import estimate as estimate_head_shoulder_metrics
from app.pipeline.keypoint_normalizer import KeypointNormalizer
from app.pipeline.leg_metrics import estimate as estimate_leg_metrics
from app.pipeline.metric_engine import CalibrationData, compute_all
from app.pipeline.pelvis_metrics import estimate as estimate_pelvis_metrics
from app.pipeline.reconstructor_3d import Reconstructor3D
from app.pipeline.spine_back_metrics import estimate as estimate_spine_back_metrics
from app.pipeline.spine_curve_model import SpineCurveModel
from app.services.dataset_service import _normalize_detector

BASE_COLUMNS = [
    "item_id",
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

DEFAULT_CALIBRATION = CalibrationData(
    patient_height_cm=170.0,
    patient_weight_kg=70.0,
    camera_height_cm=120.0,
    camera_distance_cm=200.0,
)


def _landmarks_for_pose(keypoints_json: dict | None, pose_type: str) -> list[dict]:
    if not keypoints_json:
        return []
    frames = keypoints_json.get("frame_landmarks") or []
    return [
        kp
        for kp in frames
        if (kp.get("view") or kp.get("source_view") or pose_type) == pose_type
    ]


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
    if not frame_landmarks:
        return None
    try:
        raw_keypoints = {"landmarks": frame_landmarks}
        keypoints = KeypointNormalizer.normalize(raw_keypoints, detector_model)
        calibration = DEFAULT_CALIBRATION
        keypoints_3d = Reconstructor3D.reconstruct(keypoints, None, calibration)
        spine_curve = SpineCurveModel.fit(keypoints_3d, frame_landmarks)
        pelvis_metrics = estimate_pelvis_metrics(frame_landmarks, calibration.pixels_per_mm)
        leg_metrics = estimate_leg_metrics(frame_landmarks)
        head_shoulder_metrics = estimate_head_shoulder_metrics(
            frame_landmarks, calibration.pixels_per_mm
        )
        spine_back_metrics = estimate_spine_back_metrics(
            frame_landmarks, calibration.pixels_per_mm
        )
        return compute_all(
            keypoints_3d,
            spine_curve,
            calibration,
            None,
            pelvis_metrics,
            leg_metrics,
            head_shoulder_metrics,
            spine_back_metrics,
        )
    except Exception:
        return None


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
    pose_type: DatasetPoseType | None,
    detector_model: str | None,
    status: DatasetItemStatus | None,
) -> list[DatasetItem]:
    query = select(DatasetItem)
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
    pose_type: DatasetPoseType | None,
    detector_model: str | None,
    status: DatasetItemStatus | None,
) -> tuple[str, str]:
    items = await _fetch_items(db, pose_type, detector_model, status)
    csv_content = build_dataset_csv(items)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"dataset_export_{timestamp}.csv"
    return csv_content, filename
