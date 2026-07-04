import uuid

import pytest

from app.config import settings
from app.models.patient import Patient, RiskLevel
from app.models.scan import Scan, ScanStatus
from app.services.recompute_service import recompute_scan_keypoints, reset_scan_keypoints


def _frame_landmarks() -> list[dict]:
    return [
        {"name": "left_shoulder", "x": 200, "y": 140, "confidence": 0.95, "view": "front"},
        {"name": "right_shoulder", "x": 280, "y": 140, "confidence": 0.95, "view": "front"},
        {"name": "left_hip", "x": 210, "y": 220, "confidence": 0.9, "view": "front"},
        {"name": "right_hip", "x": 270, "y": 220, "confidence": 0.9, "view": "front"},
        {"name": "left_knee", "x": 205, "y": 300, "confidence": 0.88, "view": "front"},
        {"name": "right_knee", "x": 275, "y": 300, "confidence": 0.88, "view": "front"},
        {"name": "left_ankle", "x": 200, "y": 380, "confidence": 0.85, "view": "front"},
        {"name": "right_ankle", "x": 280, "y": 380, "confidence": 0.85, "view": "front"},
        {"name": "left_ear", "x": 220, "y": 75, "confidence": 0.85, "view": "front"},
        {"name": "right_ear", "x": 260, "y": 75, "confidence": 0.85, "view": "front"},
        {"name": "jaw_midpoint", "x": 240, "y": 80, "confidence": 0.9, "view": "front"},
        {"name": "left_shoulder", "x": 305, "y": 155, "confidence": 0.95, "view": "side"},
        {"name": "right_shoulder", "x": 300, "y": 157, "confidence": 0.4, "view": "side"},
        {"name": "left_hip", "x": 292, "y": 420, "confidence": 0.9, "view": "side"},
        {"name": "right_hip", "x": 288, "y": 422, "confidence": 0.4, "view": "side"},
        {"name": "left_ear", "x": 330, "y": 100, "confidence": 0.85, "view": "side"},
        {"name": "right_ear", "x": 325, "y": 102, "confidence": 0.4, "view": "side"},
        {"name": "left_knee", "x": 288, "y": 520, "confidence": 0.88, "view": "side"},
        {"name": "right_knee", "x": 285, "y": 522, "confidence": 0.4, "view": "side"},
    ]


def _scan_and_patient() -> tuple[Scan, Patient]:
    patient = Patient(
        id=uuid.uuid4(),
        doctor_id=uuid.uuid4(),
        first_name="Test",
        last_name="Patient",
        date_of_birth="1990-01-01",
        height_cm=170,
        weight_kg=70,
        risk_level=RiskLevel.normal,
    )
    scan = Scan(
        id=uuid.uuid4(),
        patient_id=patient.id,
        doctor_id=patient.doctor_id,
        status=ScanStatus.completed,
        patient_height_cm=170.0,
        patient_weight_kg=70.0,
        detector_model=settings.detector_model,
        keypoints_json={"frame_landmarks": _frame_landmarks(), "landmarks": [], "twin_landmarks": []},
        metrics_json={"spinal_curves": {}, "normal_ranges": {}},
    )
    return scan, patient


def test_recompute_updates_audit_and_metrics(monkeypatch):
    scan, patient = _scan_and_patient()
    uploaded = {}

    monkeypatch.setattr(
        "app.services.recompute_service.storage_service.upload_bytes",
        lambda key, data, content_type: uploaded.update({"key": key, "data": data}),
    )

    edited = _frame_landmarks()
    edited[0]["x"] = 190

    result = recompute_scan_keypoints(
        scan,
        patient,
        edited,
        doctor_id=uuid.uuid4(),
        preserve_manual_spine=False,
    )

    assert result["audit"]["adjusted_at"]
    assert result["audit"]["original_frame_landmarks"]
    assert scan.metrics_json is not None
    assert "spinal_curves" in scan.metrics_json
    assert uploaded["key"]


def test_reset_restores_original_landmarks(monkeypatch):
    scan, patient = _scan_and_patient()
    monkeypatch.setattr(
        "app.services.recompute_service.storage_service.upload_bytes",
        lambda *args, **kwargs: None,
    )

    edited = [dict(item) for item in _frame_landmarks()]
    edited[0]["x"] = 150
    recompute_scan_keypoints(scan, patient, edited, doctor_id=uuid.uuid4())

    reset_scan_keypoints(scan, patient, doctor_id=uuid.uuid4())
    restored_x = next(
        kp["x"]
        for kp in scan.keypoints_json["frame_landmarks"]
        if kp["name"] == "left_shoulder" and kp["view"] == "front"
    )
    assert restored_x == 200
    assert "adjusted_at" not in scan.keypoints_json["audit"]


def test_reset_without_original_raises():
    scan, patient = _scan_and_patient()
    with pytest.raises(ValueError, match="No original keypoints"):
        reset_scan_keypoints(scan, patient)
