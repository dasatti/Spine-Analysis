import base64
import os
import uuid
from collections.abc import AsyncGenerator, Callable
from urllib.parse import urlparse, urlunparse

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database import get_db
from app.main import create_app

MINIMAL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

TEST_DB_NAME = "spinepose_test"


def _test_async_database_url() -> str:
    explicit = os.environ.get("TEST_DATABASE_URL")
    if explicit:
        return explicit
    parsed = urlparse(settings.database_url.replace("+asyncpg", ""))
    return urlunparse(parsed._replace(path=f"/{TEST_DB_NAME}")).replace(
        "postgresql://", "postgresql+asyncpg://"
    )


def _test_sync_database_url() -> str:
    url = _test_async_database_url().replace("+asyncpg", "")
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def _admin_sync_database_url() -> str:
    parsed = urlparse(_test_sync_database_url())
    return urlunparse(parsed._replace(path="/postgres"))


SYNC_DATABASE_URL = _test_sync_database_url()


def ensure_test_database() -> None:
    admin_engine = create_engine(_admin_sync_database_url(), isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": TEST_DB_NAME},
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    admin_engine.dispose()


def migrate_test_database() -> None:
    import subprocess

    env = os.environ.copy()
    env["DATABASE_URL"] = _test_async_database_url()
    subprocess.run(
        ["alembic", "upgrade", "head"],
        check=True,
        env=env,
        cwd="/app",
    )


def patch_app_database(test_async_url: str) -> None:
    import app.database as db_module

    engine = create_async_engine(test_async_url, echo=False)
    db_module.engine = engine
    db_module.AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.fixture(scope="session", autouse=True)
def configure_test_database():
    """Use an isolated test database so pytest never truncates production data."""
    test_async_url = _test_async_database_url()
    ensure_test_database()
    migrate_test_database()
    patch_app_database(test_async_url)
    yield


from app.testing.payloads import doctor_payload, patient_payload, unique_email


def truncate_tables() -> None:
    engine = create_engine(SYNC_DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE scans, patients, doctors, dataset_items RESTART IDENTITY CASCADE"))
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
    import app.database as db_module

    async with db_module.AsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        import app.database as db_module

        async with db_module.AsyncSessionLocal() as session:
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


@pytest.fixture
def single_scan_frame_file() -> dict:
    return {
        "frame_front": ("front.png", MINIMAL_PNG, "image/png"),
    }
