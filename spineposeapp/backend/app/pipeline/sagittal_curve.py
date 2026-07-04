"""Sagittal spine curvature estimation from side-view keypoints.

MediaPipe/YOLO do not detect vertebrae, so a true radiographic Cobb angle is
not obtainable. From a side-view photo we can, however, measure the gross
flexion of the trunk from the visible body landmarks (ear, shoulder, hip,
knee) and map it onto the clinical curvature scale. The result is a screening
estimate, not a diagnostic measurement.

Coordinate note: values are image pixels where y increases downward. Angle
magnitudes are orientation independent, so a left- or right-facing subject is
handled the same way.
"""

from __future__ import annotations

import math

from app.config import settings

SIDE_VIEW = "side"

# A normally standing person still has a resting curve (~20-45 deg). Surface
# landmarks only reveal additional visible flexion, so we start from a
# physiological baseline and add the measured flexion on top.
THORACIC_BASELINE_DEG = 30.0
THORACIC_GAIN = 1.2
LUMBAR_BASELINE_DEG = 30.0
LUMBAR_GAIN = 1.0

_MIN_ANGLE_DEG = 5.0
_MAX_ANGLE_DEG = 90.0


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _pick_joint(
    side_landmarks: list[dict], base_name: str, threshold: float
) -> tuple[float, float] | None:
    """Return the higher-confidence of the left/right variant of a joint."""
    candidates = [
        kp
        for kp in side_landmarks
        if kp.get("name") in (f"left_{base_name}", f"right_{base_name}")
        and float(kp.get("confidence", 0.0)) >= threshold
    ]
    if not candidates:
        return None
    best = max(candidates, key=lambda kp: float(kp.get("confidence", 0.0)))
    return float(best.get("x", 0.0)), float(best.get("y", 0.0))


def _angle_at(
    a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]
) -> float | None:
    """Interior angle (degrees) at vertex ``b`` for the path a-b-c."""
    bax, bay = a[0] - b[0], a[1] - b[1]
    bcx, bcy = c[0] - b[0], c[1] - b[1]
    norm_ba = math.hypot(bax, bay)
    norm_bc = math.hypot(bcx, bcy)
    if norm_ba < 1e-6 or norm_bc < 1e-6:
        return None
    cos_angle = (bax * bcx + bay * bcy) / (norm_ba * norm_bc)
    cos_angle = max(-1.0, min(1.0, cos_angle))
    return math.degrees(math.acos(cos_angle))


def estimate_sagittal_angles(
    frame_landmarks: list[dict],
) -> tuple[float | None, float | None]:
    """Estimate (thoracic_kyphosis, lumbar_lordosis) in degrees from side view.

    Returns ``(None, None)`` when the side frame or required landmarks are
    missing, so the caller can mark the metric unavailable rather than emit a
    misleading value.
    """
    threshold = settings.keypoint_confidence_threshold
    side = [kp for kp in frame_landmarks if kp.get("view") == SIDE_VIEW]
    if not side:
        return None, None

    ear = _pick_joint(side, "ear", threshold)
    shoulder = _pick_joint(side, "shoulder", threshold)
    hip = _pick_joint(side, "hip", threshold)
    knee = _pick_joint(side, "knee", threshold)

    thoracic: float | None = None
    if ear and shoulder and hip:
        angle = _angle_at(ear, shoulder, hip)
        if angle is not None:
            flexion = max(0.0, 180.0 - angle)
            thoracic = _clamp(
                THORACIC_BASELINE_DEG + THORACIC_GAIN * flexion,
                _MIN_ANGLE_DEG,
                _MAX_ANGLE_DEG,
            )

    lumbar: float | None = None
    if shoulder and hip and knee:
        angle = _angle_at(shoulder, hip, knee)
        if angle is not None:
            flexion = max(0.0, 180.0 - angle)
            lumbar = _clamp(
                LUMBAR_BASELINE_DEG + LUMBAR_GAIN * flexion,
                _MIN_ANGLE_DEG,
                _MAX_ANGLE_DEG,
            )

    return thoracic, lumbar
