from collections.abc import AsyncGenerator, Generator
from pathlib import Path
import shutil
import socket
import subprocess
import time
import uuid

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from psycopg import connect

from app.core.config import get_settings
from app.db.session import dispose_engine
from app.main import app

REPO_ROOT = Path(__file__).resolve().parents[2]


def _docker_is_available() -> bool:
    if shutil.which("docker") is None:
        return False

    result = subprocess.run(
        ["docker", "version"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_postgres(database_url: str, timeout_seconds: int = 60) -> None:
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        try:
            with connect(database_url) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
            return
        except Exception:
            time.sleep(1)

    raise TimeoutError("Timed out waiting for PostgreSQL container")


@pytest.fixture
def postgres_database_url(monkeypatch: pytest.MonkeyPatch) -> Generator[str, None, None]:
    if not _docker_is_available():
        pytest.skip("Docker nao esta disponivel para o teste real com PostgreSQL")

    port = _find_free_port()
    container_name = f"backend-wattio-test-postgres-{uuid.uuid4().hex[:8]}"
    database_url = f"postgresql+psycopg://postgres:postgres@127.0.0.1:{port}/wattio"
    psycopg_database_url = f"postgresql://postgres:postgres@127.0.0.1:{port}/wattio"

    subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--rm",
            "--name",
            container_name,
            "-e",
            "POSTGRES_DB=wattio",
            "-e",
            "POSTGRES_USER=postgres",
            "-e",
            "POSTGRES_PASSWORD=postgres",
            "-p",
            f"{port}:5432",
            "postgres:16-alpine",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    try:
        _wait_for_postgres(psycopg_database_url)

        monkeypatch.setenv("DATABASE_URL", database_url)
        get_settings.cache_clear()
        dispose_engine()

        alembic_config = Config(str(REPO_ROOT / "alembic.ini"))
        alembic_config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
        alembic_config.set_main_option("sqlalchemy.url", database_url)
        command.upgrade(alembic_config, "head")

        yield database_url
    finally:
        dispose_engine()
        get_settings.cache_clear()
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            check=False,
            capture_output=True,
            text=True,
        )


@pytest.fixture
async def postgres_client(
    postgres_database_url: str,
) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client


@pytest.mark.anyio
async def test_application_runs_against_real_postgresql(
    postgres_client: AsyncClient,
) -> None:
    readiness_response = await postgres_client.get("/health/ready")

    assert readiness_response.status_code == 200
    assert readiness_response.json()["checks"] == {"database": "ok"}

    create_response = await postgres_client.post(
        "/filmes",
        json={
            "title": "Alien",
            "director": "Ridley Scott",
            "year": 1979,
            "genre": "Sci-Fi",
        },
    )

    assert create_response.status_code == 201

    film_id = create_response.json()["id"]
    get_response = await postgres_client.get(f"/filmes/{film_id}")

    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Alien"
