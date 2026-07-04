import math
from dataclasses import dataclass
from typing import TypedDict

import numpy as np
import structlog

from app.config import settings
from app.pipeline.base import Keypoint
from app.pipeline.head_shoulder_metrics import HeadShoulderMetrics
from app.pipeline.leg_metrics import LegMetrics
from app.pipeline.pelvis_metrics import PelvisMetrics
from app.pipeline.spine_back_metrics import SpineBackMetrics
from app.pipeline.spine_curve_model import SpineCurve

logger = structlog.get_logger(__name__)

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


def compute_forward_head_posture(
    landmarks: list[Keypoint],
    cal: CalibrationData,
    head_shoulder_metrics: HeadShoulderMetrics | None = None,
) -> MetricResult:
    """Forward head posture from side-view ear–shoulder horizontal offset."""
    if head_shoulder_metrics is None or head_shoulder_metrics.forward_head_posture_mm is None:
        return MetricResult(
            value=None,
            unit="mm",
            availability=AVAIL_NO_LANDMARK,
            reason="Side-view estimate (no usable side frame)",
        )
    return MetricResult(
        value=round(head_shoulder_metrics.forward_head_posture_mm, 1),
        unit="mm",
        availability=AVAIL_AVAILABLE,
        reason="Side-view estimate",
    )


def compute_shoulder_height_asymmetry(
    landmarks: list[Keypoint],
    cal: CalibrationData,
    head_shoulder_metrics: HeadShoulderMetrics | None = None,
) -> MetricResult:
    """Shoulder height asymmetry from the front view."""
    if head_shoulder_metrics is None or head_shoulder_metrics.shoulder_asymmetry_mm is None:
        return MetricResult(
            value=None,
            unit="mm",
            availability=AVAIL_NO_LANDMARK,
            reason="Front-view estimate (no usable front frame)",
        )
    return MetricResult(
        value=round(head_shoulder_metrics.shoulder_asymmetry_mm, 1),
        unit="mm",
        availability=AVAIL_AVAILABLE,
        reason="Front-view estimate",
    )


def compute_spine_drift(
    landmarks: list[Keypoint],
    cal: CalibrationData,
    spine_back_metrics: SpineBackMetrics | None = None,
) -> MetricResult:
    """Spine drift from back-view deviation from the sacral midline."""
    if spine_back_metrics is None or spine_back_metrics.spine_drift_mm is None:
        return MetricResult(
            value=None,
            unit="mm",
            availability=AVAIL_NO_LANDMARK,
            reason="Back-view estimate (no usable back frame)",
        )
    return MetricResult(
        value=round(spine_back_metrics.spine_drift_mm, 1),
        unit="mm",
        availability=AVAIL_AVAILABLE,
        reason="Back-view estimate",
    )


def compute_thoracic_kyphosis(
    landmarks: list[Keypoint], spine_curve: SpineCurve, cal: CalibrationData
) -> MetricResult:
    """Sagittal thoracic kyphosis estimate from the side view.

    Requires a side-view frame; without it the true spinal curve cannot be
    approximated, so the metric is reported as unavailable rather than guessed.
    """
    if spine_curve.thoracic_angle_deg is None:
        return MetricResult(
            value=None,
            unit="°",
            availability=AVAIL_NO_LANDMARK,
            reason="Side-view estimate (no usable side frame)",
        )
    return MetricResult(
        value=round(spine_curve.thoracic_angle_deg, 1),
        unit="°",
        availability=AVAIL_AVAILABLE,
        reason="Side-view estimate",
    )


def compute_lumbar_lordosis(
    landmarks: list[Keypoint], spine_curve: SpineCurve, cal: CalibrationData
) -> MetricResult:
    """Sagittal lumbar lordosis estimate from the side view.

    Requires a side-view frame; without it the metric is reported as
    unavailable rather than guessed.
    """
    if spine_curve.lumbar_angle_deg is None:
        return MetricResult(
            value=None,
            unit="°",
            availability=AVAIL_NO_LANDMARK,
            reason="Side-view estimate (no usable side frame)",
        )
    return MetricResult(
        value=round(spine_curve.lumbar_angle_deg, 1),
        unit="°",
        availability=AVAIL_AVAILABLE,
        reason="Side-view estimate",
    )


def compute_pelvic_tilt_sagittal(
    landmarks: list[Keypoint],
    cal: CalibrationData,
    pelvis_metrics: PelvisMetrics | None = None,
) -> MetricResult:
    """Sagittal pelvic tilt estimate from the side view (hip→knee vs vertical)."""
    if pelvis_metrics is None or pelvis_metrics.tilt_sagittal_deg is None:
        return MetricResult(
            value=None,
            unit="°",
            availability=AVAIL_NO_LANDMARK,
            reason="Side-view estimate (no usable side frame)",
        )
    return MetricResult(
        value=round(pelvis_metrics.tilt_sagittal_deg, 1),
        unit="°",
        availability=AVAIL_AVAILABLE,
        reason="Side-view estimate",
    )


def compute_pelvic_obliquity(
    landmarks: list[Keypoint],
    cal: CalibrationData,
    pelvis_metrics: PelvisMetrics | None = None,
) -> MetricResult:
    """Frontal pelvic obliquity: vertical hip height difference in millimetres."""
    if pelvis_metrics is None or pelvis_metrics.obliquity_mm is None:
        return MetricResult(
            value=None,
            unit="mm",
            availability=AVAIL_NO_LANDMARK,
            reason="Front-view estimate (no usable front frame)",
        )
    return MetricResult(
        value=round(pelvis_metrics.obliquity_mm, 1),
        unit="mm",
        availability=AVAIL_AVAILABLE,
        reason="Front-view estimate",
    )


def compute_knee_flexion(
    landmarks: list[Keypoint],
    cal: CalibrationData,
    side: str,
    leg_metrics: LegMetrics | None = None,
) -> MetricResult:
    """Knee flexion estimate from front or side view (hip–knee–ankle angle)."""
    flexion = None
    if leg_metrics is not None:
        flexion = (
            leg_metrics.knee_flexion_left_deg
            if side == "left"
            else leg_metrics.knee_flexion_right_deg
        )
    if flexion is None:
        return MetricResult(
            value=None,
            unit="°",
            availability=AVAIL_NO_LANDMARK,
            reason="Front/side estimate (no usable leg chain)",
        )
    return MetricResult(
        value=round(flexion, 1),
        unit="°",
        availability=AVAIL_AVAILABLE,
        reason="Front/side estimate",
    )


def compute_hka_angle(
    landmarks: list[Keypoint],
    cal: CalibrationData,
    side: str,
    leg_metrics: LegMetrics | None = None,
) -> MetricResult:
    """Coronal HKA estimate from front or back view (hip–knee–ankle angle)."""
    angle = None
    if leg_metrics is not None:
        angle = (
            leg_metrics.hka_angle_left_deg if side == "left" else leg_metrics.hka_angle_right_deg
        )
    if angle is None:
        return MetricResult(
            value=None,
            unit="°",
            availability=AVAIL_NO_LANDMARK,
            reason="Front/back estimate (no usable leg chain)",
        )
    return MetricResult(
        value=round(angle, 1),
        unit="°",
        availability=AVAIL_AVAILABLE,
        reason="Front/back estimate",
    )


def compute_jaw_deviation(
    landmarks: list[Keypoint],
    cal: CalibrationData,
    head_shoulder_metrics: HeadShoulderMetrics | None = None,
) -> MetricResult:
    """Jaw deviation from the eye/ear facial midline in front or face view."""
    if head_shoulder_metrics is None or head_shoulder_metrics.jaw_deviation_mm is None:
        return MetricResult(
            value=None,
            unit="mm",
            availability=AVAIL_NO_FACE,
            reason="Front/face estimate (no usable face frame)",
        )
    return MetricResult(
        value=round(head_shoulder_metrics.jaw_deviation_mm, 1),
        unit="mm",
        availability=AVAIL_AVAILABLE,
        reason="Front/face estimate",
    )


def compute_adams_rib_hump(
    landmarks: list[Keypoint],
    depth_map: np.ndarray | None,
    spine_back_metrics: SpineBackMetrics | None = None,
) -> MetricResult:
    """Adams rib hump from thoracic asymmetry in the Adams forward-bend view."""
    del depth_map  # 2D Adams estimate; depth may augment this in future
    if spine_back_metrics is None or spine_back_metrics.adams_rib_hump_present is None:
        return MetricResult(
            value=None,
            unit="",
            availability=AVAIL_NO_LANDMARK,
            reason="Adams-view estimate (no usable Adams frame)",
        )
    return MetricResult(
        value=spine_back_metrics.adams_rib_hump_present,
        unit="",
        availability=AVAIL_AVAILABLE,
        reason="Adams-view estimate",
    )


def compute_vertebral_rotation(
    landmarks: list[Keypoint],
    depth_map: np.ndarray | None,
    spine_back_metrics: SpineBackMetrics | None = None,
) -> MetricResult:
    """Vertebral rotation screening index from Adams-view asymmetry."""
    del depth_map
    if spine_back_metrics is None or spine_back_metrics.vertebral_rotation_index is None:
        return MetricResult(
            value=None,
            unit="",
            availability=AVAIL_NO_LANDMARK,
            reason="Adams-view estimate (no usable Adams frame)",
        )
    return MetricResult(
        value=round(spine_back_metrics.vertebral_rotation_index, 3),
        unit="",
        availability=AVAIL_AVAILABLE,
        reason="Adams-view estimate",
    )


def compute_scapula_asymmetry(
    landmarks: list[Keypoint],
    cal: CalibrationData,
    spine_back_metrics: SpineBackMetrics | None = None,
) -> MetricResult:
    """Back-view shoulder-height asymmetry index (scapula proxy)."""
    if spine_back_metrics is None or spine_back_metrics.scapula_asymmetry_index is None:
        return MetricResult(
            value=None,
            unit="",
            availability=AVAIL_NO_LANDMARK,
            reason="Back-view estimate (no usable back frame)",
        )
    return MetricResult(
        value=round(spine_back_metrics.scapula_asymmetry_index, 3),
        unit="",
        availability=AVAIL_AVAILABLE,
        reason="Back-view estimate",
    )


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
        logger.exception("Metric computation failed", function=func.__name__, error=str(exc))
        return MetricResult(value=None, unit="", availability=AVAIL_NO_LANDMARK, reason=str(exc))


def compute_all(
    landmarks: list[Keypoint],
    spine_curve: SpineCurve,
    calibration: CalibrationData,
    depth_map: np.ndarray | None,
    pelvis_metrics: PelvisMetrics | None = None,
    leg_metrics: LegMetrics | None = None,
    head_shoulder_metrics: HeadShoulderMetrics | None = None,
    spine_back_metrics: SpineBackMetrics | None = None,
) -> MetricsJson:
    """Assemble the metrics_json structure from individual metric functions."""
    thoracic = _safe_call(compute_thoracic_kyphosis, landmarks, spine_curve, calibration)
    lumbar = _safe_call(compute_lumbar_lordosis, landmarks, spine_curve, calibration)
    pelvic_tilt = _safe_call(compute_pelvic_tilt_sagittal, landmarks, calibration, pelvis_metrics)
    pelvic_obliquity = _safe_call(compute_pelvic_obliquity, landmarks, calibration, pelvis_metrics)
    knee_left = _safe_call(compute_knee_flexion, landmarks, calibration, "left", leg_metrics)
    knee_right = _safe_call(compute_knee_flexion, landmarks, calibration, "right", leg_metrics)
    hka_left = _safe_call(compute_hka_angle, landmarks, calibration, "left", leg_metrics)
    hka_right = _safe_call(compute_hka_angle, landmarks, calibration, "right", leg_metrics)
    forward_head = _safe_call(
        compute_forward_head_posture, landmarks, calibration, head_shoulder_metrics
    )
    shoulder_asym = _safe_call(
        compute_shoulder_height_asymmetry, landmarks, calibration, head_shoulder_metrics
    )
    jaw = _safe_call(compute_jaw_deviation, landmarks, calibration, head_shoulder_metrics)
    spine_drift = _safe_call(compute_spine_drift, landmarks, calibration, spine_back_metrics)
    scapula = _safe_call(compute_scapula_asymmetry, landmarks, calibration, spine_back_metrics)
    rotation = _safe_call(compute_vertebral_rotation, landmarks, depth_map, spine_back_metrics)
    adams = _safe_call(compute_adams_rib_hump, landmarks, depth_map, spine_back_metrics)

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
