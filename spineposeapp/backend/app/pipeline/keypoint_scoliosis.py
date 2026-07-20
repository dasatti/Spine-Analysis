"""Keypoint-based scoliosis screening from back and Adams pose landmarks."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import settings
from app.pipeline.spine_back_metrics import SpineBackMetrics

SCOLIOSIS_LABEL = "scoliosis"
NORMAL_LABEL = "normal"


@dataclass(frozen=True)
class KeypointScoliosisResult:
    class_name: str
    confidence: float
    composite_score: float
    signals: dict[str, float | bool | None]


def _signal_strength(value: float | None, scale: float) -> float | None:
    if value is None or scale <= 0:
        return None
    return min(max(value / scale, 0.0), 1.0)


def estimate_keypoint_scoliosis(
    spine_back_metrics: SpineBackMetrics | None,
    pelvic_obliquity_mm: float | None = None,
) -> KeypointScoliosisResult | None:
    """Screen for scoliosis using coronal asymmetry from pose keypoints.

    Combines back-view scapula asymmetry and spine drift with Adams-view rib
    hump and rotation proxies. Returns ``None`` when no usable back/Adams data.
    """
    if spine_back_metrics is None:
        return None

    scapula = spine_back_metrics.scapula_asymmetry_index
    drift = spine_back_metrics.spine_drift_mm
    rotation = spine_back_metrics.vertebral_rotation_index
    adams_hump = spine_back_metrics.adams_rib_hump_present

    if all(v is None for v in (scapula, drift, rotation, adams_hump)):
        return None

    scapula_strength = _signal_strength(scapula, 0.10)
    drift_strength = _signal_strength(drift, 20.0)
    rotation_strength = _signal_strength(rotation, 0.05)
    adams_strength = None if adams_hump is None else (1.0 if adams_hump else 0.0)
    pelvic_strength = _signal_strength(pelvic_obliquity_mm, 15.0)

    strengths = [
        s for s in (scapula_strength, drift_strength, rotation_strength, adams_strength, pelvic_strength)
        if s is not None
    ]
    if not strengths:
        return None

    composite_score = max(strengths)

    hard_positive = False
    if adams_hump is True:
        hard_positive = True
    if scapula is not None and scapula >= settings.keypoint_scoliosis_scapula_threshold:
        hard_positive = True
    if drift is not None and drift >= settings.keypoint_scoliosis_spine_drift_mm_threshold:
        hard_positive = True
    if rotation is not None and rotation >= settings.keypoint_scoliosis_rotation_threshold:
        hard_positive = True

    positive = hard_positive or composite_score >= settings.keypoint_scoliosis_score_threshold
    class_name = SCOLIOSIS_LABEL if positive else NORMAL_LABEL

    signals: dict[str, float | bool | None] = {
        "scapula_asymmetry_index": scapula,
        "spine_drift_mm": drift,
        "vertebral_rotation_index": rotation,
        "adams_rib_hump_present": adams_hump,
        "pelvic_obliquity_mm": pelvic_obliquity_mm,
        "scapula_strength": scapula_strength,
        "drift_strength": drift_strength,
        "rotation_strength": rotation_strength,
        "adams_strength": adams_strength,
        "pelvic_strength": pelvic_strength,
    }

    return KeypointScoliosisResult(
        class_name=class_name,
        confidence=round(composite_score, 4),
        composite_score=round(composite_score, 4),
        signals=signals,
    )
