"""Tests for keypoint-based scoliosis screening."""

from app.pipeline.keypoint_scoliosis import (
    NORMAL_LABEL,
    SCOLIOSIS_LABEL,
    estimate_keypoint_scoliosis,
)
from app.pipeline.spine_back_metrics import SpineBackMetrics


def test_unavailable_when_no_spine_back_metrics():
    assert estimate_keypoint_scoliosis(None) is None


def test_unavailable_when_all_signals_missing():
    back = SpineBackMetrics(
        spine_drift_mm=None,
        scapula_asymmetry_index=None,
        vertebral_rotation_index=None,
        adams_rib_hump_present=None,
    )
    assert estimate_keypoint_scoliosis(back) is None


def test_normal_when_signals_below_threshold():
    back = SpineBackMetrics(
        spine_drift_mm=3.0,
        scapula_asymmetry_index=0.02,
        vertebral_rotation_index=0.01,
        adams_rib_hump_present=False,
    )
    result = estimate_keypoint_scoliosis(back)
    assert result is not None
    assert result.class_name == NORMAL_LABEL
    assert result.confidence < 0.45


def test_positive_on_adams_rib_hump():
    back = SpineBackMetrics(
        spine_drift_mm=None,
        scapula_asymmetry_index=None,
        vertebral_rotation_index=None,
        adams_rib_hump_present=True,
    )
    result = estimate_keypoint_scoliosis(back)
    assert result is not None
    assert result.class_name == SCOLIOSIS_LABEL
    assert result.confidence == 1.0


def test_positive_on_high_scapula_asymmetry():
    back = SpineBackMetrics(
        spine_drift_mm=None,
        scapula_asymmetry_index=0.08,
        vertebral_rotation_index=None,
        adams_rib_hump_present=None,
    )
    result = estimate_keypoint_scoliosis(back)
    assert result is not None
    assert result.class_name == SCOLIOSIS_LABEL


def test_positive_on_high_spine_drift():
    back = SpineBackMetrics(
        spine_drift_mm=15.0,
        scapula_asymmetry_index=None,
        vertebral_rotation_index=None,
        adams_rib_hump_present=None,
    )
    result = estimate_keypoint_scoliosis(back)
    assert result is not None
    assert result.class_name == SCOLIOSIS_LABEL


def test_pelvic_obliquity_contributes_to_score():
    back = SpineBackMetrics(
        spine_drift_mm=5.0,
        scapula_asymmetry_index=0.02,
        vertebral_rotation_index=None,
        adams_rib_hump_present=False,
    )
    without = estimate_keypoint_scoliosis(back)
    with_pelvis = estimate_keypoint_scoliosis(back, pelvic_obliquity_mm=20.0)
    assert without is not None and with_pelvis is not None
    assert with_pelvis.confidence >= without.confidence


def test_compute_keypoint_scoliosis_metric_unavailable():
    from app.pipeline.metric_engine import (
        AVAIL_NO_SCOLIOSIS_VIEWS,
        compute_keypoint_scoliosis_metric,
    )

    payload = compute_keypoint_scoliosis_metric(None)
    assert payload["availability"] == AVAIL_NO_SCOLIOSIS_VIEWS
    assert payload["value"] is None


def test_compute_keypoint_scoliosis_metric_available():
    from app.pipeline.metric_engine import AVAIL_AVAILABLE, compute_keypoint_scoliosis_metric

    back = SpineBackMetrics(
        spine_drift_mm=None,
        scapula_asymmetry_index=None,
        vertebral_rotation_index=None,
        adams_rib_hump_present=True,
    )
    payload = compute_keypoint_scoliosis_metric(back)
    assert payload["availability"] == AVAIL_AVAILABLE
    assert payload["value"] == SCOLIOSIS_LABEL
    assert payload["metric_type"] == "classification"
    assert "signals" in payload
