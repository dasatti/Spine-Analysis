import pytest
from httpx import AsyncClient

from tests.conftest import patient_payload


@pytest.mark.asyncio
async def test_create_patient_201(authed_client: AsyncClient):
    response = await authed_client.post("/api/v1/patients", json=patient_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["first_name"] == "Jane"
    assert body["last_name"] == "Doe"
    assert body["scan_count"] == 0


@pytest.mark.asyncio
async def test_list_patients_pagination(authed_client: AsyncClient):
    for i in range(3):
        await authed_client.post(
            "/api/v1/patients",
            json=patient_payload(
                first_name=f"Patient{i}",
                medical_record_number=f"MRN-PAGE-{i}",
            ),
        )

    page1 = await authed_client.get("/api/v1/patients", params={"page": 1, "page_size": 2})
    assert page1.status_code == 200
    body = page1.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["pages"] == 2

    page2 = await authed_client.get("/api/v1/patients", params={"page": 2, "page_size": 2})
    assert page2.status_code == 200
    assert len(page2.json()["items"]) == 1


@pytest.mark.asyncio
async def test_search_patients(authed_client: AsyncClient):
    await authed_client.post(
        "/api/v1/patients",
        json=patient_payload(first_name="Unique", last_name="Alpha"),
    )
    await authed_client.post(
        "/api/v1/patients",
        json=patient_payload(first_name="Other", last_name="Beta"),
    )

    response = await authed_client.get("/api/v1/patients", params={"search": "Unique"})
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["first_name"] == "Unique"


@pytest.mark.asyncio
async def test_get_own_patient_200(authed_client: AsyncClient, patient_id: str):
    response = await authed_client.get(f"/api/v1/patients/{patient_id}")
    assert response.status_code == 200
    assert response.json()["id"] == patient_id


@pytest.mark.asyncio
async def test_get_other_doctors_patient_404(client: AsyncClient, register_doctor):
    doctor_a = await register_doctor()
    doctor_b = await register_doctor()

    create = await client.post(
        "/api/v1/patients",
        json=patient_payload(),
        headers={"Authorization": f"Bearer {doctor_a['access_token']}"},
    )
    patient_id = create.json()["id"]

    response = await client.get(
        f"/api/v1/patients/{patient_id}",
        headers={"Authorization": f"Bearer {doctor_b['access_token']}"},
    )
    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_update_patient_200(authed_client: AsyncClient, patient_id: str):
    response = await authed_client.put(
        f"/api/v1/patients/{patient_id}",
        json={"first_name": "Janet", "height_cm": 170.0},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["first_name"] == "Janet"
    assert body["height_cm"] == 170.0


@pytest.mark.asyncio
async def test_delete_patient_soft_204(authed_client: AsyncClient, patient_id: str):
    delete = await authed_client.delete(f"/api/v1/patients/{patient_id}")
    assert delete.status_code == 204

    get = await authed_client.get(f"/api/v1/patients/{patient_id}")
    assert get.status_code == 404
