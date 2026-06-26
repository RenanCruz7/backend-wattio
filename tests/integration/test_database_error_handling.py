import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from app.api.routes.films import get_film_service
from app.main import app


class IntegrityErrorService:
    def create_film(self, payload):
        raise IntegrityError("INSERT INTO films", {}, Exception("integrity"))


class OperationalErrorService:
    def list_films(self, **kwargs):
        raise OperationalError("SELECT * FROM films", {}, Exception("db down"))


class GenericDatabaseErrorService:
    def delete_film(self, film_id: int) -> None:
        raise SQLAlchemyError("generic database error")


@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as async_client:
        yield async_client


@pytest.mark.anyio
async def test_create_film_returns_conflict_on_integrity_error(client: AsyncClient) -> None:
    app.dependency_overrides[get_film_service] = lambda: IntegrityErrorService()

    try:
        response = await client.post(
            "/filmes",
            json={
                "title": "Alien",
                "director": "Ridley Scott",
                "year": 1979,
                "genre": "Sci-Fi",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Conflito de integridade ao persistir dados no banco"
    }


@pytest.mark.anyio
async def test_list_films_returns_service_unavailable_on_operational_error(
    client: AsyncClient,
) -> None:
    app.dependency_overrides[get_film_service] = lambda: OperationalErrorService()

    try:
        response = await client.get("/filmes")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"detail": "Banco de dados indisponivel no momento"}


@pytest.mark.anyio
async def test_delete_film_returns_internal_server_error_on_generic_database_error(
    client: AsyncClient,
) -> None:
    app.dependency_overrides[get_film_service] = lambda: GenericDatabaseErrorService()

    try:
        response = await client.delete("/filmes/1")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Erro ao processar operacao no banco de dados"
    }
