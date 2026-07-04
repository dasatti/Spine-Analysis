"""Head and shoulder metrics from view-specific frame landmarks."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import settings
from app.pipeline.sagittal_curve import _pick_joint

FRONT_VIEW = "front"
FACE_VIEW = "face"
SIDE_VIEW = "side"
_JAW_VIEWS = (FRONT_VIEW, FACE_VIEW)


@dataclass
class HeadShoulderMetrics:
    forward_head_posture_mm: float | None
    shoulder_asymmetry_mm: float | None
    jaw_deviation_mm: float | None


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


def estimate_shoulder_asymmetry_mm(
    frame_landmarks: list[dict], pixels_per_mm: float | None
) -> float | None:
    """Vertical shoulder height difference in the front view (millimetres)."""
    threshold = settings.keypoint_confidence_threshold
    scale = _scale_mm_per_pixel(pixels_per_mm)
    if scale is None:
        return None

    left = _named_joint(frame_landmarks, FRONT_VIEW, "left_shoulder", threshold)
    right = _named_joint(frame_landmarks, FRONT_VIEW, "right_shoulder", threshold)
    if not left or not right:
        return None
    return abs(left[1] - right[1]) * scale


def estimate_forward_head_posture_mm(
    frame_landmarks: list[dict], pixels_per_mm: float | None
) -> float | None:
    """Anterior ear offset from shoulder in the side view (millimetres)."""
    threshold = settings.keypoint_confidence_threshold
    scale = _scale_mm_per_pixel(pixels_per_mm)
    if scale is None:
        return None

    side = [kp for kp in frame_landmarks if kp.get("view") == SIDE_VIEW]
    if not side:
        return None

    best_mm: float | None = None
    for ear_side, shoulder_side in (
        ("left_ear", "left_shoulder"),
        ("right_ear", "right_shoulder"),
    ):
        ear = _named_joint(frame_landmarks, SIDE_VIEW, ear_side, threshold)
        shoulder = _named_joint(frame_landmarks, SIDE_VIEW, shoulder_side, threshold)
        if ear and shoulder:
            mm = abs(ear[0] - shoulder[0]) * scale
            if best_mm is None or mm > best_mm:
                best_mm = mm

    if best_mm is not None:
        return best_mm

    ear = _pick_joint(side, "ear", threshold)
    shoulder = _pick_joint(side, "shoulder", threshold)
    if not ear or not shoulder:
        return None
    return abs(ear[0] - shoulder[0]) * scale


def _facial_midline_x(frame_landmarks: list[dict], view: str, threshold: float) -> float | None:
    left_eye = _named_joint(frame_landmarks, view, "left_eye", threshold)
    right_eye = _named_joint(frame_landmarks, view, "right_eye", threshold)
    if left_eye and right_eye:
        return (left_eye[0] + right_eye[0]) / 2.0

    left_ear = _named_joint(frame_landmarks, view, "left_ear", threshold)
    right_ear = _named_joint(frame_landmarks, view, "right_ear", threshold)
    if left_ear and right_ear:
        return (left_ear[0] + right_ear[0]) / 2.0

    return None


def estimate_jaw_deviation_mm(
    frame_landmarks: list[dict], pixels_per_mm: float | None
) -> float | None:
    """Horizontal jaw offset from the eye/ear midline (millimetres)."""
    threshold = settings.keypoint_confidence_threshold
    scale = _scale_mm_per_pixel(pixels_per_mm)
    if scale is None:
        return None

    for view in _JAW_VIEWS:
        midline_x = _facial_midline_x(frame_landmarks, view, threshold)
        if midline_x is None:
            continue
        jaw = _named_joint(frame_landmarks, view, "jaw_midpoint", threshold)
        if not jaw:
            nose = _named_joint(frame_landmarks, view, "nose", threshold)
            if nose:
                jaw = nose
        if not jaw:
            continue
        return abs(jaw[0] - midline_x) * scale
    return None


def estimate(frame_landmarks: list[dict], pixels_per_mm: float | None) -> HeadShoulderMetrics:
    return HeadShoulderMetrics(
        forward_head_posture_mm=estimate_forward_head_posture_mm(
            frame_landmarks, pixels_per_mm
        ),
        shoulder_asymmetry_mm=estimate_shoulder_asymmetry_mm(frame_landmarks, pixels_per_mm),
        jaw_deviation_mm=estimate_jaw_deviation_mm(frame_landmarks, pixels_per_mm),
    )
