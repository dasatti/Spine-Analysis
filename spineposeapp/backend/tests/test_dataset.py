import base64

import pytest
from httpx import AsyncClient
from sqlalchemy import update

from app.models.doctor import Doctor, DoctorRole

MINIMAL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


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
async def test_dataset_list_requires_admin(client: AsyncClient, auth_headers):
    response = await client.get("/api/v1/admin/dataset-items", headers=auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_dataset_list_empty(client: AsyncClient, admin_headers):
    response = await client.get("/api/v1/admin/dataset-items", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["items"] == []


@pytest.mark.asyncio
async def test_create_dataset_items(client: AsyncClient, admin_headers, monkeypatch):
    async def fake_process(db, item):
        item.status = __import__(
            "app.models.dataset_item", fromlist=["DatasetItemStatus"]
        ).DatasetItemStatus.ready
        item.keypoints_json = {"frame_landmarks": [], "twin_landmarks": []}
        await db.commit()
        await db.refresh(item)

    monkeypatch.setattr("app.services.dataset_service._process_item_inference", fake_process)
    monkeypatch.setattr(
        "app.services.dataset_service.storage_service.upload_bytes",
        lambda key, data, ct: key,
    )

    files = {"images": ("test.png", MINIMAL_PNG, "image/png")}
    data = {"pose_type": "front", "detector_model": "spinepose_v2"}
    response = await client.post(
        "/api/v1/admin/dataset-items",
        headers=admin_headers,
        data=data,
        files=files,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["created_count"] == 1
    assert body["items"][0]["pose_type"] == "front"
    assert body["items"][0]["image_url"]


@pytest.mark.asyncio
async def test_save_manual_labels(client: AsyncClient, admin_headers, monkeypatch):
    async def fake_process(db, item):
        from app.models.dataset_item import DatasetItemStatus

        item.status = DatasetItemStatus.ready
        item.keypoints_json = {"frame_landmarks": [], "twin_landmarks": []}
        await db.commit()
        await db.refresh(item)

    monkeypatch.setattr("app.services.dataset_service._process_item_inference", fake_process)
    monkeypatch.setattr(
        "app.services.dataset_service.storage_service.upload_bytes",
        lambda key, data, ct: key,
    )

    files = {"images": ("test.png", MINIMAL_PNG, "image/png")}
    create_resp = await client.post(
        "/api/v1/admin/dataset-items",
        headers=admin_headers,
        data={"pose_type": "front", "detector_model": "spinepose_v2"},
        files=files,
    )
    item_id = create_resp.json()["items"][0]["id"]

    response = await client.put(
        f"/api/v1/admin/dataset-items/{item_id}/manual-labels",
        headers=admin_headers,
        json={
            "thoracic_kyphosis": "yes",
            "lumbar_lordosis": "no",
            "adams_rib_hump": "na",
        },
    )
    assert response.status_code == 200, response.text
    labels = response.json()["keypoints"]["manual_labels"]
    assert labels["thoracic_kyphosis"] == "yes"
    assert labels["lumbar_lordosis"] == "no"
    assert labels["adams_rib_hump"] == "na"
    assert labels["labeled_by"]
