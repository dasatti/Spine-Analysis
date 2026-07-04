import numpy as np
import pytest

from app.pipeline.base import Keypoint
from app.pipeline.metric_engine import (
    AVAIL_AVAILABLE,
    AVAIL_NO_FACE,
    AVAIL_NO_LANDMARK,
    AVAIL_NO_SENSOR,
    CalibrationData,
    compute_adams_rib_hump,
    compute_forward_head_posture,
    compute_hka_angle,
    compute_jaw_deviation,
    compute_knee_flexion,
    compute_lumbar_lordosis,
    compute_pelvic_obliquity,
    compute_pelvic_tilt_sagittal,
    compute_scapula_asymmetry,
    compute_shoulder_height_asymmetry,
    compute_spine_drift,
    compute_thoracic_kyphosis,
    compute_vertebral_rotation,
    derive_overall_risk,
)
from app.pipeline.head_shoulder_metrics import HeadShoulderMetrics
from app.pipeline.leg_metrics import LegMetrics
from app.pipeline.pelvis_metrics import PelvisMetrics
from app.pipeline.spine_back_metrics import SpineBackMetrics
from app.pipeline.spine_curve_model import SpineCurve


def kp(
    name: str,
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
    confidence: float = 0.95,
) -> Keypoint:
    return Keypoint(
        name=name,
        x=x,
        y=y,
        confidence=confidence,
        source_view="front",
        x3d=x,
        y3d=y,
        z3d=z,
    )


@pytest.fixture
def cal() -> CalibrationData:
    return CalibrationData(
        patient_height_cm=170.0,
        patient_weight_kg=70.0,
        camera_height_cm=120.0,
        camera_distance_cm=200.0,
    )


@pytest.fixture
def leg_landmarks() -> list[Keypoint]:
    return [
        kp("left_hip", 0, 100, 0),
        kp("left_knee", 0, 50, 0),
        kp("left_ankle", 0, 0, 0),
    ]


def test_compute_forward_head_posture(cal):
    hs = HeadShoulderMetrics(forward_head_posture_mm=12.0, shoulder_asymmetry_mm=None, jaw_deviation_mm=None)
    result = compute_forward_head_posture([], cal, hs)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == 12.0


def test_compute_forward_head_posture_unavailable(cal):
    result = compute_forward_head_posture([], cal, None)
    assert result.availability == AVAIL_NO_LANDMARK


def test_compute_shoulder_height_asymmetry(cal):
    hs = HeadShoulderMetrics(forward_head_posture_mm=None, shoulder_asymmetry_mm=8.0, jaw_deviation_mm=None)
    result = compute_shoulder_height_asymmetry([], cal, hs)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == 8.0


def test_compute_spine_drift(cal):
    back = SpineBackMetrics(
        spine_drift_mm=6.0,
        scapula_asymmetry_index=None,
        vertebral_rotation_index=None,
        adams_rib_hump_present=None,
    )
    result = compute_spine_drift([], cal, back)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == 6.0


def test_compute_thoracic_kyphosis(cal):
    curve = SpineCurve(points=[], thoracic_angle_deg=32.5, lumbar_angle_deg=None)
    result = compute_thoracic_kyphosis([], curve, cal)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == 32.5


def test_compute_lumbar_lordosis(cal):
    curve = SpineCurve(points=[], thoracic_angle_deg=None, lumbar_angle_deg=28.0)
    result = compute_lumbar_lordosis([], curve, cal)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == 28.0


def test_compute_pelvic_tilt_sagittal(cal):
    pelvis = PelvisMetrics(obliquity_mm=None, tilt_sagittal_deg=9.5)
    result = compute_pelvic_tilt_sagittal([], cal, pelvis)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == 9.5


def test_compute_pelvic_tilt_sagittal_unavailable(cal):
    result = compute_pelvic_tilt_sagittal([], cal, None)
    assert result.availability == AVAIL_NO_LANDMARK


def test_compute_pelvic_obliquity(cal):
    pelvis = PelvisMetrics(obliquity_mm=6.0, tilt_sagittal_deg=None)
    result = compute_pelvic_obliquity([], cal, pelvis)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == 6.0


def test_compute_pelvic_obliquity_unavailable(cal):
    result = compute_pelvic_obliquity([], cal, None)
    assert result.availability == AVAIL_NO_LANDMARK


def test_compute_knee_flexion_left(cal):
    leg = LegMetrics(
        knee_flexion_left_deg=3.5,
        knee_flexion_right_deg=0.0,
        hka_angle_left_deg=None,
        hka_angle_right_deg=None,
    )
    result = compute_knee_flexion([], cal, "left", leg)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == 3.5


def test_compute_knee_flexion_right(cal):
    leg = LegMetrics(
        knee_flexion_left_deg=0.0,
        knee_flexion_right_deg=2.0,
        hka_angle_left_deg=None,
        hka_angle_right_deg=None,
    )
    result = compute_knee_flexion([], cal, "right", leg)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == 2.0


def test_compute_knee_flexion_unavailable(cal):
    result = compute_knee_flexion([], cal, "left", None)
    assert result.availability == AVAIL_NO_LANDMARK


def test_compute_hka_angle_left(cal):
    leg = LegMetrics(
        knee_flexion_left_deg=None,
        knee_flexion_right_deg=None,
        hka_angle_left_deg=178.5,
        hka_angle_right_deg=None,
    )
    result = compute_hka_angle([], cal, "left", leg)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == 178.5


def test_compute_hka_angle_right(cal):
    leg = LegMetrics(
        knee_flexion_left_deg=None,
        knee_flexion_right_deg=None,
        hka_angle_left_deg=None,
        hka_angle_right_deg=179.0,
    )
    result = compute_hka_angle([], cal, "right", leg)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == 179.0


def test_compute_hka_angle_unavailable(cal):
    result = compute_hka_angle([], cal, "left", None)
    assert result.availability == AVAIL_NO_LANDMARK


def test_compute_jaw_deviation(cal):
    hs = HeadShoulderMetrics(forward_head_posture_mm=None, shoulder_asymmetry_mm=None, jaw_deviation_mm=2.5)
    result = compute_jaw_deviation([], cal, hs)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == 2.5


def test_compute_jaw_deviation_no_face(cal):
    result = compute_jaw_deviation([], cal, None)
    assert result.availability == AVAIL_NO_FACE


def test_compute_adams_rib_hump(cal):
    back = SpineBackMetrics(
        spine_drift_mm=None,
        scapula_asymmetry_index=None,
        vertebral_rotation_index=None,
        adams_rib_hump_present=True,
    )
    result = compute_adams_rib_hump([], None, back)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value is True


def test_compute_adams_rib_hump_unavailable(cal):
    result = compute_adams_rib_hump([], None, None)
    assert result.availability == AVAIL_NO_LANDMARK


def test_compute_vertebral_rotation(cal):
    back = SpineBackMetrics(
        spine_drift_mm=None,
        scapula_asymmetry_index=None,
        vertebral_rotation_index=0.04,
        adams_rib_hump_present=None,
    )
    result = compute_vertebral_rotation([], None, back)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == pytest.approx(0.04)


def test_compute_scapula_asymmetry(cal):
    back = SpineBackMetrics(
        spine_drift_mm=None,
        scapula_asymmetry_index=0.08,
        vertebral_rotation_index=None,
        adams_rib_hump_present=None,
    )
    result = compute_scapula_asymmetry([], cal, back)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == pytest.approx(0.08)


def test_missing_landmarks_return_unavailable(cal):
    result = compute_forward_head_posture([], cal, None)
    assert result.availability == AVAIL_NO_LANDMARK


def test_low_confidence_landmarks(cal):
    result = compute_forward_head_posture([], cal, None)
    assert result.availability == AVAIL_NO_LANDMARK


def test_derive_overall_risk_normal():
    metrics = {
        "spinal_curves": {
            "thoracic_kyphosis_deg": {"value": 30.0, "availability": AVAIL_AVAILABLE},
        },
        "pelvis_lower_body": {},
        "head_shoulders": {},
        "spine_back": {},
        "normal_ranges": {
            "thoracic_kyphosis_deg": {"min": 20.0, "max": 45.0},
        },
    }
    assert derive_overall_risk(metrics) == "normal"


def test_derive_overall_risk_elevated():
    metrics = {
        "spinal_curves": {
            "thoracic_kyphosis_deg": {"value": 80.0, "availability": AVAIL_AVAILABLE},
        },
        "pelvis_lower_body": {},
        "head_shoulders": {},
        "spine_back": {},
        "normal_ranges": {
            "thoracic_kyphosis_deg": {"min": 20.0, "max": 45.0},
        },
    }
    assert derive_overall_risk(metrics) == "elevated"
