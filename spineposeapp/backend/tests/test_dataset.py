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


@pytest.fixture
async def research_dataset(client: AsyncClient, admin_headers):
    response = await client.post(
        "/api/v1/admin/datasets",
        headers=admin_headers,
        json={"name": "Test Dataset"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _upload_form(dataset_id: str) -> dict:
    return {
        "dataset_id": dataset_id,
        "pose_type": "front",
        "detector_model": "spinepose_v2",
    }


@pytest.mark.asyncio
async def test_research_dataset_crud(client: AsyncClient, admin_headers):
    create_resp = await client.post(
        "/api/v1/admin/datasets",
        headers=admin_headers,
        json={"name": "Training Batch A"},
    )
    assert create_resp.status_code == 201
    dataset_id = create_resp.json()["id"]

    list_resp = await client.get("/api/v1/admin/datasets", headers=admin_headers)
    assert list_resp.status_code == 200
    assert any(d["id"] == dataset_id for d in list_resp.json()["datasets"])

    update_resp = await client.put(
        f"/api/v1/admin/datasets/{dataset_id}",
        headers=admin_headers,
        json={"name": "Training Batch A (Updated)"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Training Batch A (Updated)"

    delete_resp = await client.delete(f"/api/v1/admin/datasets/{dataset_id}", headers=admin_headers)
    assert delete_resp.status_code == 204


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
async def test_create_dataset_items(client: AsyncClient, admin_headers, research_dataset, monkeypatch):
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
    data = _upload_form(research_dataset["id"])
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
    assert body["items"][0]["dataset_name"] == research_dataset["name"]
    assert body["items"][0]["image_url"]


@pytest.mark.asyncio
async def test_save_manual_labels(client: AsyncClient, admin_headers, research_dataset, monkeypatch):
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
        data=_upload_form(research_dataset["id"]),
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


@pytest.mark.asyncio
async def test_export_dataset_items_csv(client: AsyncClient, admin_headers, research_dataset, monkeypatch):
    async def fake_process(db, item):
        from app.models.dataset_item import DatasetItemStatus

        item.status = DatasetItemStatus.ready
        item.keypoints_json = {
            "frame_landmarks": [
                {
                    "name": "left_shoulder",
                    "x": 10.5,
                    "y": 20.0,
                    "confidence": 0.95,
                    "view": "front",
                }
            ],
            "twin_landmarks": [],
            "manual_labels": {"thoracic_kyphosis": "yes"},
        }
        await db.commit()
        await db.refresh(item)

    monkeypatch.setattr("app.services.dataset_service._process_item_inference", fake_process)
    monkeypatch.setattr(
        "app.services.dataset_service.storage_service.upload_bytes",
        lambda key, data, ct: key,
    )
    monkeypatch.setattr(
        "app.services.dataset_export.compute_dataset_metrics",
        lambda frame_landmarks, detector_model: {
            "spinal_curves": {"thoracic_kyphosis_deg": {"value": 42.0}},
            "pelvis_lower_body": {},
            "head_shoulders": {},
            "spine_back": {},
        },
    )

    files = {"images": ("test.png", MINIMAL_PNG, "image/png")}
    await client.post(
        "/api/v1/admin/dataset-items",
        headers=admin_headers,
        data=_upload_form(research_dataset["id"]),
        files=files,
    )

    response = await client.get(
        "/api/v1/admin/dataset-items/export",
        headers=admin_headers,
        params={"pose_type": "front"},
    )
    assert response.status_code == 200, response.text
    assert "text/csv" in response.headers.get("content-type", "")
    body = response.text
    assert "item_id" in body.splitlines()[0]
    assert "pose_type" in body.splitlines()[0]
    assert "dataset_name" in body.splitlines()[0]
    assert "left_shoulder_x" in body.splitlines()[0]
    assert "thoracic_kyphosis_deg" in body.splitlines()[0]
    assert "manual_thoracic_kyphosis" in body.splitlines()[0]
    assert "10.5" in body
    assert "yes" in body


@pytest.mark.asyncio
async def test_get_dataset_item_includes_metrics(
    client: AsyncClient, admin_headers, research_dataset, monkeypatch
):
    sample_metrics = {
        "spinal_curves": {"thoracic_kyphosis_deg": {"value": 35.0, "unit": "deg", "availability": "available"}},
        "pelvis_lower_body": {},
        "head_shoulders": {},
        "spine_back": {},
        "normal_ranges": {},
    }

    async def fake_process(db, item):
        from app.models.dataset_item import DatasetItemStatus

        item.status = DatasetItemStatus.ready
        item.keypoints_json = {
            "frame_landmarks": [{"name": "left_shoulder", "x": 1, "y": 2, "confidence": 0.9, "view": "front"}],
            "twin_landmarks": [],
        }
        await db.commit()
        await db.refresh(item)

    monkeypatch.setattr("app.services.dataset_service._process_item_inference", fake_process)
    monkeypatch.setattr(
        "app.services.dataset_service.storage_service.upload_bytes",
        lambda key, data, ct: key,
    )
    monkeypatch.setattr(
        "app.services.dataset_service.metrics_for_item",
        lambda item: sample_metrics,
    )

    files = {"images": ("test.png", MINIMAL_PNG, "image/png")}
    create_resp = await client.post(
        "/api/v1/admin/dataset-items",
        headers=admin_headers,
        data=_upload_form(research_dataset["id"]),
        files=files,
    )
    item_id = create_resp.json()["items"][0]["id"]

    response = await client.get(f"/api/v1/admin/dataset-items/{item_id}", headers=admin_headers)
    assert response.status_code == 200, response.text
    assert response.json()["metrics"]["spinal_curves"]["thoracic_kyphosis_deg"]["value"] == 35.0
