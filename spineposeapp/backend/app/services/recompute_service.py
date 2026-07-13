"""Recompute scan metrics from edited frame landmarks (no re-detection)."""

from __future__ import annotations

import copy
import json
import uuid
from dataclasses import asdict
from datetime import UTC, datetime

from app.models.patient import Patient, RiskLevel
from app.models.scan import Scan
from app.pipeline.head_shoulder_metrics import estimate as estimate_head_shoulder_metrics
from app.pipeline.keypoint_normalizer import KeypointNormalizer
from app.pipeline.landmark_refresh import refresh_frame_landmarks
from app.pipeline.landmark_mapping import twin_landmarks_from_frame
from app.pipeline.leg_metrics import estimate as estimate_leg_metrics
from app.pipeline.metric_engine import CalibrationData, compute_all, derive_overall_risk
from app.pipeline.metric_engine import preserve_ai_classification
from app.pipeline.pelvis_metrics import estimate as estimate_pelvis_metrics
from app.pipeline.reconstructor_3d import Reconstructor3D
from app.pipeline.spine_back_metrics import estimate as estimate_spine_back_metrics
from app.pipeline.spine_curve_model import SpineCurveModel
from app.services.storage_service import storage_service

RISK_RANK = {
    RiskLevel.normal: 0,
    RiskLevel.monitor: 1,
    RiskLevel.elevated: 2,
}


def _keypoints_to_json(keypoints: list) -> list[dict]:
    return [asdict(kp) for kp in keypoints]


def _rebuild_twin_landmarks(frame_landmarks: list[dict]) -> list[dict]:
    """Rebuild twin from edited front, side, and back frame keypoints."""
    return twin_landmarks_from_frame(frame_landmarks)


def _persist_twin_landmarks(scan: Scan, twin_landmarks: list[dict]) -> None:
    twin_key = scan.digital_twin_url or f"scans/{scan.id}/twin/keypoints.json"
    storage_service.upload_bytes(
        twin_key,
        json.dumps(twin_landmarks).encode("utf-8"),
        "application/json",
    )
    scan.digital_twin_url = twin_key


def _worsen_patient_risk(patient: Patient, new_risk_value: str) -> None:
    new_risk = RiskLevel(new_risk_value)
    if RISK_RANK[new_risk] > RISK_RANK[patient.risk_level]:
        patient.risk_level = new_risk


def _ensure_audit(keypoints_json: dict | None) -> dict:
    audit = {}
    if isinstance(keypoints_json, dict):
        audit = copy.deepcopy(keypoints_json.get("audit") or {})
    audit.setdefault("history", [])
    return audit


def compute_metrics_bundle(
    scan: Scan,
    frame_landmarks: list[dict],
) -> tuple[dict, list, list[dict]]:
    """Run normalisation → 3D → metrics for a frame_landmarks list."""
    raw_keypoints = {"landmarks": frame_landmarks}
    keypoints = KeypointNormalizer.normalize(raw_keypoints, scan.detector_model)
    calibration = CalibrationData(
        patient_height_cm=scan.patient_height_cm,
        patient_weight_kg=scan.patient_weight_kg,
        camera_height_cm=scan.camera_height_cm,
        camera_distance_cm=scan.camera_distance_cm,
    )
    keypoints_3d = Reconstructor3D.reconstruct(keypoints, None, calibration)
    spine_curve = SpineCurveModel.fit(keypoints_3d, frame_landmarks)
    pelvis_metrics = estimate_pelvis_metrics(frame_landmarks, calibration.pixels_per_mm)
    leg_metrics = estimate_leg_metrics(frame_landmarks)
    head_shoulder_metrics = estimate_head_shoulder_metrics(
        frame_landmarks, calibration.pixels_per_mm
    )
    spine_back_metrics = estimate_spine_back_metrics(
        frame_landmarks, calibration.pixels_per_mm
    )
    metrics = compute_all(
        keypoints_3d,
        spine_curve,
        calibration,
        None,
        pelvis_metrics,
        leg_metrics,
        head_shoulder_metrics,
        spine_back_metrics,
    )
    return metrics, keypoints_3d, frame_landmarks


def recompute_scan_keypoints(
    scan: Scan,
    patient: Patient,
    frame_landmarks: list[dict],
    *,
    doctor_id: uuid.UUID | None = None,
    preserve_manual_spine: bool = False,
    refresh_synthetics: bool = True,
    views_refreshed: list[str] | None = None,
    note: str | None = None,
) -> dict:
    """Recompute metrics and persist updated keypoints on the scan."""
    prior_keypoints = copy.deepcopy(scan.keypoints_json or {})
    audit = _ensure_audit(prior_keypoints)

    if not audit.get("original_frame_landmarks"):
        audit["original_frame_landmarks"] = copy.deepcopy(
            prior_keypoints.get("frame_landmarks") or frame_landmarks
        )
        audit["original_twin_landmarks"] = copy.deepcopy(
            prior_keypoints.get("twin_landmarks") or []
        )

    working_landmarks = copy.deepcopy(frame_landmarks)
    if refresh_synthetics:
        working_landmarks = refresh_frame_landmarks(
            working_landmarks,
            views=views_refreshed,
            preserve_manual_spine=preserve_manual_spine,
        )

    metrics, keypoints_3d, working_landmarks = compute_metrics_bundle(scan, working_landmarks)
    metrics = preserve_ai_classification(metrics, scan.metrics_json)
    overall_risk = derive_overall_risk(metrics)

    twin_landmarks = _rebuild_twin_landmarks(working_landmarks)

    audit["adjusted_at"] = datetime.now(UTC).isoformat()
    if doctor_id:
        audit["adjusted_by"] = str(doctor_id)
    audit["preserve_manual_spine"] = preserve_manual_spine
    audit["twin_rebuilt"] = True
    audit["history"] = list(audit.get("history") or [])[-19:] + [
        {
            "at": audit["adjusted_at"],
            "by": audit.get("adjusted_by"),
            "action": "manual_recompute",
            "note": note,
            "views_refreshed": views_refreshed,
            "preserve_manual_spine": preserve_manual_spine,
        }
    ]

    scan.metrics_json = metrics
    scan.overall_risk = RiskLevel(overall_risk)
    scan.keypoints_json = {
        "landmarks": _keypoints_to_json(keypoints_3d),
        "frame_landmarks": working_landmarks,
        "twin_landmarks": twin_landmarks,
        "audit": audit,
    }
    _persist_twin_landmarks(scan, twin_landmarks)
    _worsen_patient_risk(patient, overall_risk)
    return scan.keypoints_json


def reset_scan_keypoints(
    scan: Scan,
    patient: Patient,
    *,
    doctor_id: uuid.UUID | None = None,
    note: str | None = None,
) -> dict:
    """Restore detector-original keypoints and recompute metrics."""
    prior_keypoints = scan.keypoints_json or {}
    audit = _ensure_audit(prior_keypoints)
    original = audit.get("original_frame_landmarks")
    if not original:
        raise ValueError("No original keypoints stored for this scan")

    original_twin = audit.get("original_twin_landmarks")
    frame_landmarks = copy.deepcopy(original)
    metrics, keypoints_3d, frame_landmarks = compute_metrics_bundle(scan, frame_landmarks)
    metrics = preserve_ai_classification(metrics, scan.metrics_json)
    overall_risk = derive_overall_risk(metrics)

    twin_landmarks = (
        copy.deepcopy(original_twin)
        if original_twin
        else _rebuild_twin_landmarks(frame_landmarks)
    )

    audit.pop("adjusted_at", None)
    audit.pop("adjusted_by", None)
    audit.pop("preserve_manual_spine", None)
    audit.pop("twin_rebuilt", None)
    audit["history"] = list(audit.get("history") or []) + [
        {
            "at": datetime.now(UTC).isoformat(),
            "by": str(doctor_id) if doctor_id else None,
            "action": "reset_keypoints",
            "note": note,
        }
    ]

    scan.metrics_json = metrics
    scan.overall_risk = RiskLevel(overall_risk)
    scan.keypoints_json = {
        "landmarks": _keypoints_to_json(keypoints_3d),
        "frame_landmarks": frame_landmarks,
        "twin_landmarks": twin_landmarks,
        "audit": audit,
    }
    _persist_twin_landmarks(scan, twin_landmarks)
    _worsen_patient_risk(patient, overall_risk)
    return scan.keypoints_json
