import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes.health import database_health_check
from app.main import app


@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as async_client:
        yield async_client


@pytest.mark.anyio
async def test_liveness_returns_application_metadata(client: AsyncClient) -> None:
    response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "app": "Wattio Films API",
        "version": "0.1.0",
        "checks": None,
    }


@pytest.mark.anyio
async def test_healthcheck_returns_database_status_when_ready(client: AsyncClient) -> None:
    app.dependency_overrides[database_health_check] = lambda: True

    try:
        response = await client.get("/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "app": "Wattio Films API",
        "version": "0.1.0",
        "checks": {"database": "ok"},
    }


@pytest.mark.anyio
async def test_readiness_returns_service_unavailable_when_database_is_down(
    client: AsyncClient,
) -> None:
    app.dependency_overrides[database_health_check] = lambda: False

    try:
        response = await client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "status": "degraded",
        "app": "Wattio Films API",
        "version": "0.1.0",
        "checks": {"database": "unavailable"},
    }
