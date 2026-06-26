import uuid
from datetime import UTC, date, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.patient import Gender, Patient, RiskLevel
from app.models.scan import Scan, ScanStatus


@pytest.mark.asyncio
async def test_summary_counts_correct(
    authed_client: AsyncClient,
    db_session: AsyncSession,
    registered_doctor: dict,
):
    doctor_id = uuid.UUID(registered_doctor["doctor"]["id"])
    now = datetime.now(UTC)

    active_patient = Patient(
        doctor_id=doctor_id,
        first_name="Active",
        last_name="One",
        date_of_birth=date(1990, 1, 1),
        gender=Gender.female,
        height_cm=165.0,
        weight_kg=60.0,
    )
    inactive_patient = Patient(
        doctor_id=doctor_id,
        first_name="Inactive",
        last_name="Two",
        date_of_birth=date(1988, 2, 2),
        gender=Gender.male,
        height_cm=175.0,
        weight_kg=75.0,
        is_active=False,
    )
    db_session.add_all([active_patient, inactive_patient])
    await db_session.flush()

    scans = [
        Scan(
            patient_id=active_patient.id,
            doctor_id=doctor_id,
            status=ScanStatus.completed,
            patient_height_cm=165.0,
            patient_weight_kg=60.0,
            detector_model=settings.detector_model,
            overall_risk=RiskLevel.monitor,
            created_at=now,
            completed_at=now,
        ),
        Scan(
            patient_id=active_patient.id,
            doctor_id=doctor_id,
            status=ScanStatus.completed,
            patient_height_cm=165.0,
            patient_weight_kg=60.0,
            detector_model=settings.detector_model,
            overall_risk=RiskLevel.elevated,
            created_at=now,
            completed_at=now,
        ),
        Scan(
            patient_id=active_patient.id,
            doctor_id=doctor_id,
            status=ScanStatus.pending,
            patient_height_cm=165.0,
            patient_weight_kg=60.0,
            detector_model=settings.detector_model,
            created_at=now,
        ),
    ]
    db_session.add_all(scans)
    await db_session.commit()

    response = await authed_client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["total_patients"] == 1
    assert body["scans_today"] == 3
    assert body["pending_reports"] == 2
    assert body["sessions_this_month"] == 3
