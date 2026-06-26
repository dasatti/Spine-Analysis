import numpy as np
import pytest

from app.pipeline.base import Keypoint
from app.pipeline.metric_engine import (
    AVAIL_AVAILABLE,
    AVAIL_LOW_CONFIDENCE,
    AVAIL_NO_DEPTH,
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
    landmarks = [kp("left_ear", 0, 180, 20), kp("left_shoulder", 0, 150, 0)]
    result = compute_forward_head_posture(landmarks, cal)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == 20.0


def test_compute_shoulder_height_asymmetry(cal):
    landmarks = [kp("left_shoulder", 0, 160, 0), kp("right_shoulder", 0, 150, 0)]
    result = compute_shoulder_height_asymmetry(landmarks, cal)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == 10.0


def test_compute_spine_drift(cal):
    landmarks = [
        kp("spine_c7", 0, 170, 0),
        kp("spine_t4", 5, 150, 0),
        kp("spine_l3", 10, 100, 0),
    ]
    result = compute_spine_drift(landmarks, cal)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == 10.0


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
    landmarks = [kp("left_hip", 0, 100, 0), kp("right_hip", 0, 100, 10)]
    result = compute_pelvic_tilt_sagittal(landmarks, cal)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == pytest.approx(7.0)


def test_compute_pelvic_obliquity(cal):
    landmarks = [kp("left_hip", 0, 105, 0), kp("right_hip", 0, 100, 0)]
    result = compute_pelvic_obliquity(landmarks, cal)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == 5.0


def test_compute_knee_flexion_left(cal, leg_landmarks):
    result = compute_knee_flexion(leg_landmarks, cal, "left")
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == 0.0


def test_compute_knee_flexion_right(cal):
    landmarks = [
        kp("right_hip", 0, 100, 0),
        kp("right_knee", 0, 50, 0),
        kp("right_ankle", 0, 0, 0),
    ]
    result = compute_knee_flexion(landmarks, cal, "right")
    assert result.availability == AVAIL_AVAILABLE


def test_compute_hka_angle_left(cal, leg_landmarks):
    result = compute_hka_angle(leg_landmarks, cal, "left")
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == 180.0


def test_compute_hka_angle_right(cal):
    landmarks = [
        kp("right_hip", 0, 100, 0),
        kp("right_knee", 0, 50, 0),
        kp("right_ankle", 0, 0, 0),
    ]
    result = compute_hka_angle(landmarks, cal, "right")
    assert result.availability == AVAIL_AVAILABLE


def test_compute_jaw_deviation(cal):
    landmarks = [kp("jaw_midpoint", 5, 180, 0), kp("facial_midline", 0, 180, 0)]
    result = compute_jaw_deviation(landmarks, cal)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == 5.0


def test_compute_jaw_deviation_no_face(cal):
    result = compute_jaw_deviation([], cal)
    assert result.availability == AVAIL_NO_FACE


def test_compute_adams_rib_hump(cal):
    landmarks = [kp("left_shoulder", 0, 160, 0), kp("right_shoulder", 0, 160, 10)]
    depth = np.zeros((10, 10))
    result = compute_adams_rib_hump(landmarks, depth)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value is True


def test_compute_adams_rib_hump_no_depth(cal):
    landmarks = [kp("left_shoulder", 0, 160, 0), kp("right_shoulder", 0, 160, 0)]
    result = compute_adams_rib_hump(landmarks, None)
    assert result.availability == AVAIL_NO_DEPTH


def test_compute_vertebral_rotation(cal):
    landmarks = [kp("left_shoulder", 0, 160, 0), kp("right_shoulder", 0, 160, 20)]
    depth = np.zeros((10, 10))
    result = compute_vertebral_rotation(landmarks, depth)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == pytest.approx(0.05)


def test_compute_scapula_asymmetry(cal):
    landmarks = [kp("left_shoulder", 0, 160, 0), kp("right_shoulder", 0, 150, 0)]
    result = compute_scapula_asymmetry(landmarks, cal)
    assert result.availability == AVAIL_AVAILABLE
    assert result.value == pytest.approx(0.1)


def test_missing_landmarks_return_unavailable(cal):
    result = compute_forward_head_posture([], cal)
    assert result.availability == AVAIL_NO_LANDMARK


def test_low_confidence_landmarks(cal):
    landmarks = [
        kp("left_ear", 0, 180, 20, confidence=0.1),
        kp("left_shoulder", 0, 150, 0, confidence=0.1),
    ]
    result = compute_forward_head_posture(landmarks, cal)
    assert result.availability == AVAIL_LOW_CONFIDENCE


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
