import pytest
from httpx import AsyncClient
from sqlalchemy import update

from app.models.doctor import Doctor, DoctorRole


@pytest.fixture
async def admin_headers(registered_doctor, db_session):
    await db_session.execute(
        update(Doctor)
        .where(Doctor.email == registered_doctor["_email"])
        .values(role=DoctorRole.admin.value)
    )
    await db_session.commit()
    return {"Authorization": f"Bearer {registered_doctor['access_token']}"}


@pytest.mark.asyncio
async def test_admin_analytics_requires_admin(client: AsyncClient, auth_headers):
    response = await client.get("/api/v1/admin/analytics/summary", headers=auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_analytics_success(client: AsyncClient, admin_headers):
    response = await client.get("/api/v1/admin/analytics/summary", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert "total_doctors" in body
    assert "total_patients" in body
    assert body["total_doctors"] >= 1


@pytest.mark.asyncio
async def test_admin_list_doctors(client: AsyncClient, admin_headers):
    response = await client.get("/api/v1/admin/doctors", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert len(body["items"]) >= 1


@pytest.mark.asyncio
async def test_admin_update_doctor(client: AsyncClient, admin_headers, registered_doctor):
    doctor_id = registered_doctor["doctor"]["id"]
    response = await client.put(
        f"/api/v1/admin/doctors/{doctor_id}",
        headers=admin_headers,
        json={"first_name": "Updated", "specialty": "Orthopedics"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["first_name"] == "Updated"
    assert body["specialty"] == "Orthopedics"


@pytest.mark.asyncio
async def test_register_includes_role(client: AsyncClient):
    from app.testing.payloads import doctor_payload

    payload = doctor_payload()
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    assert response.json()["doctor"]["role"] == "doctor"
