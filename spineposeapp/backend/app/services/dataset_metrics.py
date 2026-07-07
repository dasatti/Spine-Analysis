"""Compute posture metrics from dataset item keypoints."""

from __future__ import annotations

from app.models.dataset_item import DatasetItem, DatasetItemStatus
from app.pipeline.head_shoulder_metrics import estimate as estimate_head_shoulder_metrics
from app.pipeline.keypoint_normalizer import KeypointNormalizer
from app.pipeline.leg_metrics import estimate as estimate_leg_metrics
from app.pipeline.metric_engine import CalibrationData, compute_all
from app.pipeline.pelvis_metrics import estimate as estimate_pelvis_metrics
from app.pipeline.reconstructor_3d import Reconstructor3D
from app.pipeline.spine_back_metrics import estimate as estimate_spine_back_metrics
from app.pipeline.spine_curve_model import SpineCurveModel

DEFAULT_CALIBRATION = CalibrationData(
    patient_height_cm=170.0,
    patient_weight_kg=70.0,
    camera_height_cm=120.0,
    camera_distance_cm=200.0,
)


def landmarks_for_pose(keypoints_json: dict | None, pose_type: str) -> list[dict]:
    if not keypoints_json:
        return []
    frames = keypoints_json.get("frame_landmarks") or []
    return [
        kp
        for kp in frames
        if (kp.get("view") or kp.get("source_view") or pose_type) == pose_type
    ]


def compute_dataset_metrics(frame_landmarks: list[dict], detector_model: str) -> dict | None:
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


def metrics_for_item(item: DatasetItem) -> dict | None:
    if item.status != DatasetItemStatus.ready:
        return None
    frame_landmarks = landmarks_for_pose(item.keypoints_json, item.pose_type.value)
    return compute_dataset_metrics(frame_landmarks, item.detector_model)
