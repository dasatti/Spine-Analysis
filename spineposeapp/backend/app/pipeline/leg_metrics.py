"""Lower-limb metrics from view-specific frame landmarks.

Knee flexion is measured as 180° minus the hip–knee–ankle angle in a single
capture view (front preferred, side as fallback). HKA (coronal limb alignment)
uses the hip–knee–ankle angle in the front or back view only.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config import settings
from app.pipeline.sagittal_curve import _angle_at

FRONT_VIEW = "front"
BACK_VIEW = "back"
SIDE_VIEW = "side"
_KNEE_FLEXION_VIEWS = (FRONT_VIEW, SIDE_VIEW)
_HKA_VIEWS = (FRONT_VIEW, BACK_VIEW)


@dataclass
class LegMetrics:
    knee_flexion_left_deg: float | None
    knee_flexion_right_deg: float | None
    hka_angle_left_deg: float | None
    hka_angle_right_deg: float | None


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


def _leg_chain_angle(
    frame_landmarks: list[dict], view: str, side: str, threshold: float
) -> float | None:
    hip = _named_joint(frame_landmarks, view, f"{side}_hip", threshold)
    knee = _named_joint(frame_landmarks, view, f"{side}_knee", threshold)
    ankle = _named_joint(frame_landmarks, view, f"{side}_ankle", threshold)
    if not hip or not knee or not ankle:
        return None
    return _angle_at(hip, knee, ankle)


def estimate_knee_flexion_deg(frame_landmarks: list[dict], side: str) -> float | None:
    """Knee flexion for one leg from a single view (front, then side)."""
    threshold = settings.keypoint_confidence_threshold
    for view in _KNEE_FLEXION_VIEWS:
        angle = _leg_chain_angle(frame_landmarks, view, side, threshold)
        if angle is not None:
            return max(0.0, 180.0 - angle)
    return None


def estimate_hka_angle_deg(frame_landmarks: list[dict], side: str) -> float | None:
    """Coronal HKA angle for one leg from front or back view."""
    threshold = settings.keypoint_confidence_threshold
    for view in _HKA_VIEWS:
        angle = _leg_chain_angle(frame_landmarks, view, side, threshold)
        if angle is not None:
            return angle
    return None


def estimate(frame_landmarks: list[dict]) -> LegMetrics:
    return LegMetrics(
        knee_flexion_left_deg=estimate_knee_flexion_deg(frame_landmarks, "left"),
        knee_flexion_right_deg=estimate_knee_flexion_deg(frame_landmarks, "right"),
        hka_angle_left_deg=estimate_hka_angle_deg(frame_landmarks, "left"),
        hka_angle_right_deg=estimate_hka_angle_deg(frame_landmarks, "right"),
    )
