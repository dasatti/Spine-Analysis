import base64
import uuid
from collections.abc import AsyncGenerator, Callable

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal, get_db
from app.main import create_app

MINIMAL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

SYNC_DATABASE_URL = settings.database_url.replace("+asyncpg", "")


def unique_email(prefix: str = "doctor") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def doctor_payload(**overrides) -> dict:
    payload = {
        "email": unique_email(),
        "password": "SecurePass1",
        "first_name": "Alice",
        "last_name": "Smith",
        "specialty": "Orthopedics",
        "license_number": "LIC-001",
        "clinic_name": "Spine Clinic",
        "country": "US",
        "city": "Boston",
    }
    payload.update(overrides)
    return payload


def patient_payload(**overrides) -> dict:
    payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": "1990-01-15",
        "gender": "female",
        "height_cm": 165.0,
        "weight_kg": 60.0,
        "medical_record_number": f"MRN-{uuid.uuid4().hex[:6]}",
    }
    payload.update(overrides)
    return payload


def truncate_tables() -> None:
    engine = create_engine(SYNC_DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE scans, patients, doctors RESTART IDENTITY CASCADE"))
    engine.dispose()


@pytest.fixture(autouse=True)
def mock_celery_delay(monkeypatch):
    monkeypatch.setattr(
        "app.workers.scan_tasks.process_scan.delay",
        lambda *_args, **_kwargs: None,
    )


@pytest.fixture(autouse=True)
def clean_db():
    truncate_tables()
    yield
    truncate_tables()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with AsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def register_doctor(client: AsyncClient) -> Callable[..., dict]:
    async def _register(**overrides) -> dict:
        payload = doctor_payload(**overrides)
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 201, response.text
        body = response.json()
        body["_password"] = payload["password"]
        body["_email"] = payload["email"]
        return body

    return _register


@pytest.fixture
async def registered_doctor(register_doctor):
    return await register_doctor()


@pytest.fixture
async def auth_headers(registered_doctor) -> dict[str, str]:
    return {"Authorization": f"Bearer {registered_doctor['access_token']}"}


@pytest.fixture
async def authed_client(client: AsyncClient, auth_headers: dict[str, str]) -> AsyncClient:
    client.headers.update(auth_headers)
    return client


@pytest.fixture
async def patient_id(authed_client: AsyncClient) -> str:
    response = await authed_client.post("/api/v1/patients", json=patient_payload())
    assert response.status_code == 201, response.text
    return response.json()["id"]


@pytest.fixture
def scan_frame_files() -> dict:
    return {
        "frame_front": ("front.png", MINIMAL_PNG, "image/png"),
        "frame_side": ("side.png", MINIMAL_PNG, "image/png"),
        "frame_back": ("back.png", MINIMAL_PNG, "image/png"),
        "frame_adams": ("adams.png", MINIMAL_PNG, "image/png"),
    }
