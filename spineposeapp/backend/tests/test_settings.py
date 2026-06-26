import pytest
from httpx import AsyncClient

from app.config import settings


@pytest.mark.asyncio
async def test_get_settings_200(authed_client: AsyncClient):
    response = await authed_client.get("/api/v1/settings")
    assert response.status_code == 200
    body = response.json()
    assert body["detector_model"] == settings.detector_model
    assert body["keypoint_confidence_threshold"] == settings.keypoint_confidence_threshold
    assert body["model_weights_loaded"] is True
