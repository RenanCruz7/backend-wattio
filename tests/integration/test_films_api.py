from collections.abc import AsyncGenerator, Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture
def session_factory() -> Generator[sessionmaker[Session], None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    try:
        yield factory
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
async def client(
    session_factory: sessionmaker[Session],
) -> AsyncGenerator[AsyncClient, None]:
    def override_get_db() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as async_client:
        yield async_client

    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_post_filmes_creates_record(client: AsyncClient) -> None:
    response = await client.post(
        "/filmes",
        json={
            "title": "Alien",
            "director": "Ridley Scott",
            "year": 1979,
            "genre": "Sci-Fi",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["title"] == "Alien"


@pytest.mark.anyio
async def test_get_filmes_lists_records(client: AsyncClient) -> None:
    await client.post(
        "/filmes",
        json={
            "title": "Alien",
            "director": "Ridley Scott",
            "year": 1979,
            "genre": "Sci-Fi",
        },
    )
    await client.post(
        "/filmes",
        json={
            "title": "Blade Runner",
            "director": "Ridley Scott",
            "year": 1982,
            "genre": "Sci-Fi",
        },
    )

    response = await client.get("/filmes")

    assert response.status_code == 200
    assert [film["title"] for film in response.json()] == ["Alien", "Blade Runner"]


@pytest.mark.anyio
async def test_get_filmes_by_id_returns_correct_item(client: AsyncClient) -> None:
    create_response = await client.post(
        "/filmes",
        json={
            "title": "Alien",
            "director": "Ridley Scott",
            "year": 1979,
            "genre": "Sci-Fi",
        },
    )

    film_id = create_response.json()["id"]
    response = await client.get(f"/filmes/{film_id}")

    assert response.status_code == 200
    assert response.json()["id"] == film_id
    assert response.json()["title"] == "Alien"


@pytest.mark.anyio
async def test_get_filmes_by_id_returns_404_when_missing(client: AsyncClient) -> None:
    response = await client.get("/filmes/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Filme com id 999 nao encontrado"}


@pytest.mark.anyio
async def test_put_filmes_updates_record(client: AsyncClient) -> None:
    create_response = await client.post(
        "/filmes",
        json={
            "title": "Alien",
            "director": "Ridley Scott",
            "year": 1979,
            "genre": "Sci-Fi",
        },
    )

    film_id = create_response.json()["id"]
    response = await client.put(
        f"/filmes/{film_id}",
        json={"title": "Alien Remastered", "year": 2003},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Alien Remastered"
    assert response.json()["year"] == 2003
    assert response.json()["director"] == "Ridley Scott"


@pytest.mark.anyio
async def test_delete_filmes_removes_record(client: AsyncClient) -> None:
    create_response = await client.post(
        "/filmes",
        json={
            "title": "Alien",
            "director": "Ridley Scott",
            "year": 1979,
            "genre": "Sci-Fi",
        },
    )

    film_id = create_response.json()["id"]
    delete_response = await client.delete(f"/filmes/{film_id}")
    get_response = await client.get(f"/filmes/{film_id}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert get_response.status_code == 404
