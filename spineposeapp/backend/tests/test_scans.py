import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.scan import Scan, ScanStatus
from app.testing.payloads import patient_payload


@pytest.mark.asyncio
async def test_create_scan_202(
    authed_client: AsyncClient,
    patient_id: str,
    scan_frame_files: dict,
):
    data = {
        "patient_id": patient_id,
        "patient_height_cm": "165",
        "patient_weight_kg": "60",
        "capture_device": "test-camera",
    }
    response = await authed_client.post("/api/v1/scans", data=data, files=scan_frame_files)
    assert response.status_code == 202
    body = response.json()
    assert body["patient_id"] == patient_id
    assert body["status"] == "pending"
    assert body["detector_model"] == settings.detector_model


@pytest.mark.asyncio
async def test_poll_status_returns_progress_message(
    authed_client: AsyncClient,
    patient_id: str,
    scan_frame_files: dict,
):
    create = await authed_client.post(
        "/api/v1/scans",
        data={
            "patient_id": patient_id,
            "patient_height_cm": "165",
            "patient_weight_kg": "60",
        },
        files=scan_frame_files,
    )
    scan_id = create.json()["id"]

    response = await authed_client.get(f"/api/v1/scans/{scan_id}/status")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending"
    assert body["progress_message"] == "Queued for processing"


@pytest.mark.asyncio
async def test_get_scan_with_metrics_200(
    authed_client: AsyncClient,
    db_session: AsyncSession,
    registered_doctor: dict,
    patient_id: str,
):
    doctor_id = uuid.UUID(registered_doctor["doctor"]["id"])
    patient_uuid = uuid.UUID(patient_id)

    scan = Scan(
        id=uuid.uuid4(),
        patient_id=patient_uuid,
        doctor_id=doctor_id,
        status=ScanStatus.completed,
        patient_height_cm=165.0,
        patient_weight_kg=60.0,
        detector_model=settings.detector_model,
        progress_message="Complete",
        metrics_json={
            "spinal_curves": {
                "thoracic_kyphosis_deg": {
                    "value": 30.0,
                    "unit": "°",
                    "availability": "available",
                }
            },
            "normal_ranges": {},
        },
    )
    db_session.add(scan)
    await db_session.commit()

    response = await authed_client.get(f"/api/v1/scans/{scan.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["metrics"]["spinal_curves"]["thoracic_kyphosis_deg"]["value"] == 30.0


@pytest.mark.asyncio
async def test_delete_scan_while_processing_409(
    authed_client: AsyncClient,
    db_session: AsyncSession,
    registered_doctor: dict,
    patient_id: str,
):
    doctor_id = uuid.UUID(registered_doctor["doctor"]["id"])
    patient_uuid = uuid.UUID(patient_id)

    scan = Scan(
        id=uuid.uuid4(),
        patient_id=patient_uuid,
        doctor_id=doctor_id,
        status=ScanStatus.processing,
        patient_height_cm=165.0,
        patient_weight_kg=60.0,
        detector_model=settings.detector_model,
        progress_message="Processing",
    )
    db_session.add(scan)
    await db_session.commit()

    response = await authed_client.delete(f"/api/v1/scans/{scan.id}")
    assert response.status_code == 409
    assert response.json()["code"] == "SCAN_PROCESSING"


@pytest.mark.asyncio
async def test_recompute_scan_keypoints(
    authed_client: AsyncClient,
    db_session: AsyncSession,
    registered_doctor: dict,
    patient_id: str,
):
    doctor_id = uuid.UUID(registered_doctor["doctor"]["id"])
    patient_uuid = uuid.UUID(patient_id)
    frame_landmarks = [
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
    ]

    scan = Scan(
        id=uuid.uuid4(),
        patient_id=patient_uuid,
        doctor_id=doctor_id,
        status=ScanStatus.completed,
        patient_height_cm=165.0,
        patient_weight_kg=60.0,
        detector_model=settings.detector_model,
        keypoints_json={"frame_landmarks": frame_landmarks, "landmarks": [], "twin_landmarks": []},
        metrics_json={"spinal_curves": {}, "normal_ranges": {}},
    )
    db_session.add(scan)
    await db_session.commit()

    payload = {
        "frame_landmarks": [{**frame_landmarks[0], "x": 190}, *frame_landmarks[1:]],
        "preserve_manual_spine": False,
        "refresh_synthetics": True,
    }
    response = await authed_client.post(f"/api/v1/scans/{scan.id}/recompute", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["keypoints_adjusted"] is True
    assert body["keypoints"]["audit"]["adjusted_at"]
    assert body["metrics"] is not None


@pytest.mark.asyncio
async def test_list_scans_filtered_by_patient(
    authed_client: AsyncClient,
    patient_id: str,
    scan_frame_files: dict,
):
    other = await authed_client.post("/api/v1/patients", json=patient_payload(first_name="Other"))
    other_patient_id = other.json()["id"]

    await authed_client.post(
        "/api/v1/scans",
        data={
            "patient_id": patient_id,
            "patient_height_cm": "165",
            "patient_weight_kg": "60",
        },
        files=scan_frame_files,
    )
    await authed_client.post(
        "/api/v1/scans",
        data={
            "patient_id": other_patient_id,
            "patient_height_cm": "180",
            "patient_weight_kg": "80",
        },
        files=scan_frame_files,
    )

    response = await authed_client.get("/api/v1/scans", params={"patient_id": patient_id})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["patient_id"] == patient_id
