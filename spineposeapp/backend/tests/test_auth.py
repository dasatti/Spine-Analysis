import pytest
from httpx import AsyncClient

from tests.conftest import doctor_payload


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    payload = doctor_payload()
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["doctor"]["email"] == payload["email"]
    assert body["doctor"]["first_name"] == payload["first_name"]


@pytest.mark.asyncio
async def test_register_duplicate_email_409(client: AsyncClient):
    payload = doctor_payload()
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json()["code"] == "EMAIL_EXISTS"


@pytest.mark.asyncio
async def test_register_weak_password_422(client: AsyncClient):
    payload = doctor_payload(password="weak")
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, register_doctor):
    doctor = await register_doctor()
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": doctor["_email"], "password": doctor["_password"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["doctor"]["email"] == doctor["_email"]


@pytest.mark.asyncio
async def test_login_wrong_password_401(client: AsyncClient, register_doctor):
    doctor = await register_doctor()
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": doctor["_email"], "password": "WrongPass1"},
    )
    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_me_returns_profile(authed_client: AsyncClient):
    response = await authed_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    body = response.json()
    assert body["email"]
    assert body["first_name"] == "Alice"
    assert body["last_name"] == "Smith"


@pytest.mark.asyncio
async def test_me_unauthenticated_401(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
