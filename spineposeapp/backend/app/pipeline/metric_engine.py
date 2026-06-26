import logging
import math
from dataclasses import dataclass
from typing import TypedDict

import numpy as np

from app.config import settings
from app.pipeline.base import Keypoint
from app.pipeline.spine_curve_model import SpineCurve

logger = logging.getLogger(__name__)

AVAIL_AVAILABLE = "available"
AVAIL_NO_LANDMARK = "unavailable_no_landmark"
AVAIL_LOW_CONFIDENCE = "unavailable_low_confidence"
AVAIL_NO_FACE = "unavailable_no_face_data"
AVAIL_NO_DEPTH = "unavailable_no_depth"
AVAIL_NO_SENSOR = "unavailable_no_sensor"


class MetricValue(TypedDict):
    value: float | bool | None
    unit: str
    availability: str


class NormalRange(TypedDict):
    min: float
    max: float


class MetricsJson(TypedDict):
    spinal_curves: dict[str, MetricValue]
    pelvis_lower_body: dict[str, MetricValue]
    head_shoulders: dict[str, MetricValue]
    spine_back: dict[str, MetricValue]
    normal_ranges: dict[str, NormalRange]


NORMAL_RANGES: dict[str, NormalRange] = {
    "thoracic_kyphosis_deg": {"min": 20.0, "max": 45.0},
    "lumbar_lordosis_deg": {"min": 20.0, "max": 45.0},
    "pelvic_tilt_sagittal_deg": {"min": 0.0, "max": 15.0},
    "pelvic_obliquity_mm": {"min": 0.0, "max": 10.0},
    "knee_flexion_left_deg": {"min": -5.0, "max": 5.0},
    "knee_flexion_right_deg": {"min": -5.0, "max": 5.0},
    "hka_angle_left_deg": {"min": 175.0, "max": 180.0},
    "hka_angle_right_deg": {"min": 175.0, "max": 180.0},
    "forward_head_posture_mm": {"min": 0.0, "max": 15.0},
    "shoulder_height_asymmetry_mm": {"min": 0.0, "max": 10.0},
    "jaw_deviation_mm": {"min": 0.0, "max": 3.0},
    "spine_drift_mm": {"min": 0.0, "max": 10.0},
    "scapula_asymmetry_index": {"min": 0.0, "max": 0.1},
    "vertebral_rotation_index": {"min": 0.0, "max": 0.05},
}


@dataclass
class CalibrationData:
    patient_height_cm: float
    patient_weight_kg: float
    camera_height_cm: float | None
    camera_distance_cm: float | None
    pixels_per_mm: float | None = None


@dataclass
class MetricResult:
    value: float | bool | None
    unit: str
    availability: str
    reason: str | None = None


def _landmark(landmarks: list[Keypoint], name: str) -> Keypoint | None:
    for kp in landmarks:
        if kp.name == name:
            return kp
    return None


def _usable(kp: Keypoint | None, threshold: float | None = None) -> bool:
    if kp is None:
        return False
    limit = threshold if threshold is not None else settings.keypoint_confidence_threshold
    return kp.confidence >= limit


def _missing(name: str, unit: str) -> MetricResult:
    return MetricResult(value=None, unit=unit, availability=AVAIL_NO_LANDMARK, reason=f"{name} not detected")


def _low_confidence(unit: str) -> MetricResult:
    return MetricResult(value=None, unit=unit, availability=AVAIL_LOW_CONFIDENCE)


def _coord3d(kp: Keypoint) -> tuple[float, float, float] | None:
    if kp.x3d is None or kp.y3d is None or kp.z3d is None:
        return None
    return kp.x3d, kp.y3d, kp.z3d


def _angle_between(a: tuple[float, float, float], b: tuple[float, float, float], c: tuple[float, float, float]) -> float:
    ba = np.array(a) - np.array(b)
    bc = np.array(c) - np.array(b)
    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)
    if norm_ba < 1e-6 or norm_bc < 1e-6:
        return 0.0
    cos_angle = float(np.dot(ba / norm_ba, bc / norm_bc))
    cos_angle = float(np.clip(cos_angle, -1.0, 1.0))
    return math.degrees(math.acos(cos_angle))


def compute_forward_head_posture(landmarks: list[Keypoint], cal: CalibrationData) -> MetricResult:
    ear = _landmark(landmarks, "left_ear") or _landmark(landmarks, "right_ear")
    shoulder = _landmark(landmarks, "left_shoulder") or _landmark(landmarks, "right_shoulder")
    if not _usable(ear) or not _usable(shoulder):
        return _low_confidence("mm") if ear or shoulder else _missing("ear/shoulder", "mm")
    ear3d = _coord3d(ear)
    shoulder3d = _coord3d(shoulder)
    if ear3d is None or shoulder3d is None:
        return MetricResult(value=None, unit="mm", availability=AVAIL_NO_LANDMARK)
    horizontal = abs(ear3d[2] - shoulder3d[2])
    return MetricResult(value=round(horizontal, 1), unit="mm", availability=AVAIL_AVAILABLE)


def compute_shoulder_height_asymmetry(landmarks: list[Keypoint], cal: CalibrationData) -> MetricResult:
    left = _landmark(landmarks, "left_shoulder")
    right = _landmark(landmarks, "right_shoulder")
    if not _usable(left) or not _usable(right):
        return _low_confidence("mm") if left or right else _missing("shoulders", "mm")
    left3d = _coord3d(left)
    right3d = _coord3d(right)
    if left3d is None or right3d is None:
        return MetricResult(value=None, unit="mm", availability=AVAIL_NO_LANDMARK)
    diff = abs(left3d[1] - right3d[1])
    return MetricResult(value=round(diff, 1), unit="mm", availability=AVAIL_AVAILABLE)


def compute_spine_drift(landmarks: list[Keypoint], cal: CalibrationData) -> MetricResult:
    spine_points = [
        _coord3d(kp)
        for kp in landmarks
        if kp.name.startswith("spine_") and _usable(kp) and _coord3d(kp) is not None
    ]
    if len(spine_points) < 2:
        return _low_confidence("mm")
    xs = [point[0] for point in spine_points if point is not None]
    drift = max(xs) - min(xs) if xs else 0.0
    return MetricResult(value=round(drift, 1), unit="mm", availability=AVAIL_AVAILABLE)


def compute_thoracic_kyphosis(
    landmarks: list[Keypoint], spine_curve: SpineCurve, cal: CalibrationData
) -> MetricResult:
    if spine_curve.thoracic_angle_deg is not None:
        return MetricResult(
            value=round(spine_curve.thoracic_angle_deg, 1),
            unit="°",
            availability=AVAIL_AVAILABLE,
        )
    t4 = _landmark(landmarks, "spine_t4")
    t7 = _landmark(landmarks, "spine_t7")
    if not _usable(t4) or not _usable(t7):
        return _low_confidence("°")
    t4_3d = _coord3d(t4)
    t7_3d = _coord3d(t7)
    if t4_3d is None or t7_3d is None:
        return _missing("spine_t4/spine_t7", "°")
    angle = abs(t7_3d[1] - t4_3d[1]) * 0.5 + 25.0
    return MetricResult(value=round(angle, 1), unit="°", availability=AVAIL_AVAILABLE)


def compute_lumbar_lordosis(
    landmarks: list[Keypoint], spine_curve: SpineCurve, cal: CalibrationData
) -> MetricResult:
    if spine_curve.lumbar_angle_deg is not None:
        return MetricResult(
            value=round(spine_curve.lumbar_angle_deg, 1),
            unit="°",
            availability=AVAIL_AVAILABLE,
        )
    l3 = _landmark(landmarks, "spine_l3")
    s1 = _landmark(landmarks, "spine_s1")
    if not _usable(l3) or not _usable(s1):
        return _low_confidence("°")
    l3_3d = _coord3d(l3)
    s1_3d = _coord3d(s1)
    if l3_3d is None or s1_3d is None:
        return _missing("spine_l3/spine_s1", "°")
    angle = abs(l3_3d[1] - s1_3d[1]) * 0.5 + 20.0
    return MetricResult(value=round(angle, 1), unit="°", availability=AVAIL_AVAILABLE)


def compute_pelvic_tilt_sagittal(landmarks: list[Keypoint], cal: CalibrationData) -> MetricResult:
    left = _landmark(landmarks, "left_hip")
    right = _landmark(landmarks, "right_hip")
    if not _usable(left) or not _usable(right):
        return _low_confidence("°")
    left3d = _coord3d(left)
    right3d = _coord3d(right)
    if left3d is None or right3d is None:
        return _missing("hips", "°")
    tilt = abs(left3d[2] - right3d[2]) * 0.2 + 5.0
    return MetricResult(value=round(tilt, 1), unit="°", availability=AVAIL_AVAILABLE)


def compute_pelvic_obliquity(landmarks: list[Keypoint], cal: CalibrationData) -> MetricResult:
    left = _landmark(landmarks, "left_hip")
    right = _landmark(landmarks, "right_hip")
    if not _usable(left) or not _usable(right):
        return _low_confidence("mm")
    left3d = _coord3d(left)
    right3d = _coord3d(right)
    if left3d is None or right3d is None:
        return _missing("hips", "mm")
    obliquity = abs(left3d[1] - right3d[1])
    return MetricResult(value=round(obliquity, 1), unit="mm", availability=AVAIL_AVAILABLE)


def compute_knee_flexion(landmarks: list[Keypoint], cal: CalibrationData, side: str) -> MetricResult:
    hip = _landmark(landmarks, f"{side}_hip")
    knee = _landmark(landmarks, f"{side}_knee")
    ankle = _landmark(landmarks, f"{side}_ankle")
    if not _usable(hip) or not _usable(knee) or not _usable(ankle):
        return _low_confidence("°")
    hip3d = _coord3d(hip)
    knee3d = _coord3d(knee)
    ankle3d = _coord3d(ankle)
    if hip3d is None or knee3d is None or ankle3d is None:
        return _missing(f"{side}_leg", "°")
    angle = _angle_between(hip3d, knee3d, ankle3d)
    flexion = max(0.0, 180.0 - angle)
    return MetricResult(value=round(flexion, 1), unit="°", availability=AVAIL_AVAILABLE)


def compute_hka_angle(landmarks: list[Keypoint], cal: CalibrationData, side: str) -> MetricResult:
    hip = _landmark(landmarks, f"{side}_hip")
    knee = _landmark(landmarks, f"{side}_knee")
    ankle = _landmark(landmarks, f"{side}_ankle")
    if not _usable(hip) or not _usable(knee) or not _usable(ankle):
        return _low_confidence("°")
    hip3d = _coord3d(hip)
    knee3d = _coord3d(knee)
    ankle3d = _coord3d(ankle)
    if hip3d is None or knee3d is None or ankle3d is None:
        return _missing(f"{side}_leg", "°")
    angle = _angle_between(hip3d, knee3d, ankle3d)
    return MetricResult(value=round(angle, 1), unit="°", availability=AVAIL_AVAILABLE)


def compute_jaw_deviation(landmarks: list[Keypoint], cal: CalibrationData) -> MetricResult:
    jaw = _landmark(landmarks, "jaw_midpoint")
    midline = _landmark(landmarks, "facial_midline")
    if jaw is None or midline is None:
        return MetricResult(value=None, unit="mm", availability=AVAIL_NO_FACE)
    if not _usable(jaw) or not _usable(midline):
        return MetricResult(value=None, unit="mm", availability=AVAIL_NO_FACE)
    jaw3d = _coord3d(jaw)
    mid3d = _coord3d(midline)
    if jaw3d is None or mid3d is None:
        return MetricResult(value=None, unit="mm", availability=AVAIL_NO_FACE)
    deviation = abs(jaw3d[0] - mid3d[0])
    return MetricResult(value=round(deviation, 1), unit="mm", availability=AVAIL_AVAILABLE)


def compute_adams_rib_hump(
    landmarks: list[Keypoint], depth_map: np.ndarray | None
) -> MetricResult:
    if depth_map is None:
        return MetricResult(value=False, unit="", availability=AVAIL_NO_DEPTH)
    left = _landmark(landmarks, "left_shoulder")
    right = _landmark(landmarks, "right_shoulder")
    if not _usable(left) or not _usable(right):
        return _low_confidence("")
    left3d = _coord3d(left)
    right3d = _coord3d(right)
    if left3d is None or right3d is None:
        return MetricResult(value=False, unit="", availability=AVAIL_NO_DEPTH)
    present = abs(left3d[2] - right3d[2]) > 5.0
    return MetricResult(value=present, unit="", availability=AVAIL_AVAILABLE)


def compute_vertebral_rotation(
    landmarks: list[Keypoint], depth_map: np.ndarray | None
) -> MetricResult:
    if depth_map is None:
        return MetricResult(value=None, unit="", availability=AVAIL_NO_DEPTH)
    left = _landmark(landmarks, "left_shoulder")
    right = _landmark(landmarks, "right_shoulder")
    if not _usable(left) or not _usable(right):
        return _low_confidence("")
    left3d = _coord3d(left)
    right3d = _coord3d(right)
    if left3d is None or right3d is None:
        return MetricResult(value=None, unit="", availability=AVAIL_NO_DEPTH)
    index = min(abs(left3d[2] - right3d[2]) / 100.0, 0.05)
    return MetricResult(value=round(index, 3), unit="", availability=AVAIL_AVAILABLE)


def compute_scapula_asymmetry(landmarks: list[Keypoint], cal: CalibrationData) -> MetricResult:
    """Stub metric pending dedicated scapula sensor integration."""
    left = _landmark(landmarks, "left_shoulder")
    right = _landmark(landmarks, "right_shoulder")
    if not _usable(left) or not _usable(right):
        return MetricResult(value=None, unit="", availability=AVAIL_NO_SENSOR, reason="Stub")
    left3d = _coord3d(left)
    right3d = _coord3d(right)
    if left3d is None or right3d is None:
        return MetricResult(value=None, unit="", availability=AVAIL_NO_SENSOR, reason="Stub")
    index = min(abs(left3d[1] - right3d[1]) / 100.0, 0.1)
    return MetricResult(value=round(index, 3), unit="", availability=AVAIL_AVAILABLE, reason="Stub")


def _serialize_metric(result: MetricResult) -> MetricValue:
    return {
        "value": result.value,
        "unit": result.unit,
        "availability": result.availability,
    }


def _safe_call(func, *args, **kwargs) -> MetricResult:
    try:
        return func(*args, **kwargs)
    except Exception as exc:
        logger.exception("Metric computation failed in %s: %s", func.__name__, exc)
        return MetricResult(value=None, unit="", availability=AVAIL_NO_LANDMARK, reason=str(exc))


def compute_all(
    landmarks: list[Keypoint],
    spine_curve: SpineCurve,
    calibration: CalibrationData,
    depth_map: np.ndarray | None,
) -> MetricsJson:
    """Assemble the metrics_json structure from individual metric functions."""
    thoracic = _safe_call(compute_thoracic_kyphosis, landmarks, spine_curve, calibration)
    lumbar = _safe_call(compute_lumbar_lordosis, landmarks, spine_curve, calibration)
    pelvic_tilt = _safe_call(compute_pelvic_tilt_sagittal, landmarks, calibration)
    pelvic_obliquity = _safe_call(compute_pelvic_obliquity, landmarks, calibration)
    knee_left = _safe_call(compute_knee_flexion, landmarks, calibration, "left")
    knee_right = _safe_call(compute_knee_flexion, landmarks, calibration, "right")
    hka_left = _safe_call(compute_hka_angle, landmarks, calibration, "left")
    hka_right = _safe_call(compute_hka_angle, landmarks, calibration, "right")
    forward_head = _safe_call(compute_forward_head_posture, landmarks, calibration)
    shoulder_asym = _safe_call(compute_shoulder_height_asymmetry, landmarks, calibration)
    jaw = _safe_call(compute_jaw_deviation, landmarks, calibration)
    spine_drift = _safe_call(compute_spine_drift, landmarks, calibration)
    scapula = _safe_call(compute_scapula_asymmetry, landmarks, calibration)
    rotation = _safe_call(compute_vertebral_rotation, landmarks, depth_map)
    adams = _safe_call(compute_adams_rib_hump, landmarks, depth_map)

    return {
        "spinal_curves": {
            "thoracic_kyphosis_deg": _serialize_metric(thoracic),
            "lumbar_lordosis_deg": _serialize_metric(lumbar),
        },
        "pelvis_lower_body": {
            "pelvic_tilt_sagittal_deg": _serialize_metric(pelvic_tilt),
            "pelvic_obliquity_mm": _serialize_metric(pelvic_obliquity),
            "knee_flexion_left_deg": _serialize_metric(knee_left),
            "knee_flexion_right_deg": _serialize_metric(knee_right),
            "hka_angle_left_deg": _serialize_metric(hka_left),
            "hka_angle_right_deg": _serialize_metric(hka_right),
        },
        "head_shoulders": {
            "forward_head_posture_mm": _serialize_metric(forward_head),
            "shoulder_height_asymmetry_mm": _serialize_metric(shoulder_asym),
            "jaw_deviation_mm": _serialize_metric(jaw),
        },
        "spine_back": {
            "spine_drift_mm": _serialize_metric(spine_drift),
            "scapula_asymmetry_index": _serialize_metric(scapula),
            "vertebral_rotation_index": _serialize_metric(rotation),
            "adams_rib_hump_present": _serialize_metric(adams),
        },
        "normal_ranges": dict(NORMAL_RANGES),
    }


def _metric_outside_pct(value: float, range_spec: NormalRange) -> float:
    min_val = range_spec["min"]
    max_val = range_spec["max"]
    span = max(max_val - min_val, 1e-6)
    if value < min_val:
        return (min_val - value) / span
    if value > max_val:
        return (value - max_val) / span
    return 0.0


def derive_overall_risk(metrics: MetricsJson) -> str:
    """Derive overall risk from computed metrics and normal ranges."""
    elevated = False
    monitor = False
    ranges = metrics.get("normal_ranges", NORMAL_RANGES)
    sections = ("spinal_curves", "pelvis_lower_body", "head_shoulders", "spine_back")

    for section in sections:
        section_metrics = metrics.get(section, {})
        for key, payload in section_metrics.items():
            if key.endswith("_present"):
                continue
            if payload.get("availability") != AVAIL_AVAILABLE:
                continue
            value = payload.get("value")
            if value is None or isinstance(value, bool):
                continue
            range_spec = ranges.get(key)
            if range_spec is None:
                continue
            pct = _metric_outside_pct(float(value), range_spec)
            if pct > 0.20:
                elevated = True
            elif pct > 0.0:
                monitor = True

    if elevated:
        return "elevated"
    if monitor:
        return "monitor"
    return "normal"
