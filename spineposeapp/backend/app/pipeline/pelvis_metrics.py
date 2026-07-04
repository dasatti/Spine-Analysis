"""Frontal and sagittal pelvic metrics from view-specific frame landmarks.

Pose models do not output ASIS/PSIS, so these are screening estimates:
- Obliquity: vertical height difference between hips in the front view (mm).
- Sagittal tilt: thigh inclination from vertical in the side view (degrees).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.config import settings
from app.pipeline.sagittal_curve import _pick_joint

FRONT_VIEW = "front"
SIDE_VIEW = "side"


@dataclass
class PelvisMetrics:
    obliquity_mm: float | None
    tilt_sagittal_deg: float | None


def _named_hip(
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


def estimate_pelvic_obliquity_mm(
    frame_landmarks: list[dict], pixels_per_mm: float | None
) -> float | None:
    """Vertical hip height difference in the frontal plane (millimetres)."""
    threshold = settings.keypoint_confidence_threshold
    scale = _scale_mm_per_pixel(pixels_per_mm)
    if scale is None:
        return None

    left = _named_hip(frame_landmarks, FRONT_VIEW, "left_hip", threshold)
    right = _named_hip(frame_landmarks, FRONT_VIEW, "right_hip", threshold)
    if not left or not right:
        return None

    return abs(left[1] - right[1]) * scale


def estimate_pelvic_tilt_sagittal_deg(frame_landmarks: list[dict]) -> float | None:
    """Thigh inclination from vertical in the side view (degrees).

    Uses the visible hip→knee segment as a proxy for anterior/posterior pelvic
    orientation when ASIS/PSIS landmarks are unavailable.
    """
    threshold = settings.keypoint_confidence_threshold
    side = [kp for kp in frame_landmarks if kp.get("view") == SIDE_VIEW]
    if not side:
        return None

    hip = _pick_joint(side, "hip", threshold)
    knee = _pick_joint(side, "knee", threshold)
    if not hip or not knee:
        return None

    dx = knee[0] - hip[0]
    dy = knee[1] - hip[1]
    if abs(dy) < 1e-6:
        return None

    return math.degrees(math.atan2(abs(dx), abs(dy)))


def estimate(frame_landmarks: list[dict], pixels_per_mm: float | None) -> PelvisMetrics:
    return PelvisMetrics(
        obliquity_mm=estimate_pelvic_obliquity_mm(frame_landmarks, pixels_per_mm),
        tilt_sagittal_deg=estimate_pelvic_tilt_sagittal_deg(frame_landmarks),
    )
