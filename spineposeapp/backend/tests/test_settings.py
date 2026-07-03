import pytest
from httpx import AsyncClient

from app.config import settings


@pytest.mark.asyncio
async def test_get_settings_200(authed_client: AsyncClient):
    response = await authed_client.get("/api/v1/settings")
    assert response.status_code == 200
    body = response.json()
    assert body["detector_model"] == settings.detector_model
    assert body["default_detector_model"] == settings.detector_model
    assert body["keypoint_confidence_threshold"] == settings.keypoint_confidence_threshold
    assert isinstance(body["available_detectors"], list)
    assert len(body["available_detectors"]) >= 2


@pytest.mark.asyncio
async def test_update_detector_settings(authed_client: AsyncClient):
    response = await authed_client.put(
        "/api/v1/settings/detector",
        json={"detector_model": "spinepose_v2"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["detector_model"] == "spinepose_v2"
    assert body["preferred_detector_model"] == "spinepose_v2"
