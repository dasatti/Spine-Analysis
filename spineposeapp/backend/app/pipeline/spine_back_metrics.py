"""Spine and back metrics from view-specific frame landmarks."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import settings
from app.pipeline.landmark_mapping import SPINE_CHAIN

BACK_VIEW = "back"
ADAMS_VIEW = "adams"
ADAMS_RIB_HUMP_THRESHOLD_MM = 8.0


@dataclass
class SpineBackMetrics:
    spine_drift_mm: float | None
    scapula_asymmetry_index: float | None
    vertebral_rotation_index: float | None
    adams_rib_hump_present: bool | None


def _named_joint(
    frame_landmarks: list[dict], view: str, name: str, threshold: float
) -> tuple[float, float] | None:
    for kp in frame_landmarks:
        if kp.get("view") != view or kp.get("name") != name:
            continue
        if float(kp.get("confidence", 0.0)) < threshold:
            continue
        return float(kp.get("x", 0.0)), float(kp.get("y", 0.0))
    return None


def _scale_mm_per_pixel(pixels_per_mm: float | None) -> float | None:
    if pixels_per_mm is None or pixels_per_mm <= 0:
        return None
    return pixels_per_mm


def _spine_midline_x(
    frame_landmarks: list[dict], view: str, threshold: float
) -> float | None:
    left_hip = _named_joint(frame_landmarks, view, "left_hip", threshold)
    right_hip = _named_joint(frame_landmarks, view, "right_hip", threshold)
    if left_hip and right_hip:
        return (left_hip[0] + right_hip[0]) / 2.0
    sacrum = _named_joint(frame_landmarks, view, "spine_s1", threshold)
    if sacrum:
        return sacrum[0]
    return None


def estimate_spine_drift_mm(
    frame_landmarks: list[dict], pixels_per_mm: float | None
) -> float | None:
    """Max horizontal spine offset from the sacral midline in the back view."""
    threshold = settings.keypoint_confidence_threshold
    scale = _scale_mm_per_pixel(pixels_per_mm)
    if scale is None:
        return None

    midline_x = _spine_midline_x(frame_landmarks, BACK_VIEW, threshold)
    if midline_x is None:
        return None

    spine_points: list[tuple[float, float]] = []
    for name in SPINE_CHAIN:
        point = _named_joint(frame_landmarks, BACK_VIEW, name, threshold)
        if point:
            spine_points.append(point)

    if len(spine_points) < 2:
        return None

    max_dev_px = max(abs(point[0] - midline_x) for point in spine_points)
    return max_dev_px * scale


def _adams_shoulder_asymmetry_mm(
    frame_landmarks: list[dict], pixels_per_mm: float | None
) -> float | None:
    threshold = settings.keypoint_confidence_threshold
    scale = _scale_mm_per_pixel(pixels_per_mm)
    if scale is None:
        return None

    left = _named_joint(frame_landmarks, ADAMS_VIEW, "left_shoulder", threshold)
    right = _named_joint(frame_landmarks, ADAMS_VIEW, "right_shoulder", threshold)
    if not left or not right:
        return None
    return abs(left[1] - right[1]) * scale


def estimate_adams_rib_hump_present(
    frame_landmarks: list[dict], pixels_per_mm: float | None
) -> bool | None:
    """Rib hump proxy from thoracic shoulder-height asymmetry in Adams view."""
    asymmetry_mm = _adams_shoulder_asymmetry_mm(frame_landmarks, pixels_per_mm)
    if asymmetry_mm is None:
        return None
    return asymmetry_mm >= ADAMS_RIB_HUMP_THRESHOLD_MM


def estimate_vertebral_rotation_index(
    frame_landmarks: list[dict], pixels_per_mm: float | None
) -> float | None:
    """Rotation index from Adams-view thoracic asymmetry (screening scale)."""
    asymmetry_mm = _adams_shoulder_asymmetry_mm(frame_landmarks, pixels_per_mm)
    if asymmetry_mm is None:
        return None
    return min(asymmetry_mm / 100.0, 0.05)


def estimate_scapula_asymmetry_index(
    frame_landmarks: list[dict], pixels_per_mm: float | None
) -> float | None:
    """Back-view shoulder height asymmetry normalised by shoulder width."""
    del pixels_per_mm  # index is scale-free
    threshold = settings.keypoint_confidence_threshold
    left = _named_joint(frame_landmarks, BACK_VIEW, "left_shoulder", threshold)
    right = _named_joint(frame_landmarks, BACK_VIEW, "right_shoulder", threshold)
    if not left or not right:
        return None

    shoulder_width = abs(left[0] - right[0])
    if shoulder_width < 1e-6:
        return None
    return min(abs(left[1] - right[1]) / shoulder_width, 0.1)


def estimate(frame_landmarks: list[dict], pixels_per_mm: float | None) -> SpineBackMetrics:
    return SpineBackMetrics(
        spine_drift_mm=estimate_spine_drift_mm(frame_landmarks, pixels_per_mm),
        scapula_asymmetry_index=estimate_scapula_asymmetry_index(
            frame_landmarks, pixels_per_mm
        ),
        vertebral_rotation_index=estimate_vertebral_rotation_index(
            frame_landmarks, pixels_per_mm
        ),
        adams_rib_hump_present=estimate_adams_rib_hump_present(
            frame_landmarks, pixels_per_mm
        ),
    )
