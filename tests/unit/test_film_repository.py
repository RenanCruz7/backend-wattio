from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.film import Film
from app.repositories.film_repository import FilmRepository


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    db_session = session_factory()

    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_repository_creates_and_fetches_film(session: Session) -> None:
    repository = FilmRepository(session)

    created_film = repository.create(
        {
            "title": "Alien",
            "director": "Ridley Scott",
            "year": 1979,
            "genre": "Sci-Fi",
        }
    )

    fetched_film = repository.get_by_id(created_film.id)

    assert created_film.id is not None
    assert created_film.created_at is not None
    assert fetched_film is not None
    assert fetched_film.title == "Alien"


def test_repository_lists_films_in_id_order(session: Session) -> None:
    repository = FilmRepository(session)

    repository.create(
        {
            "title": "Alien",
            "director": "Ridley Scott",
            "year": 1979,
            "genre": "Sci-Fi",
        }
    )
    repository.create(
        {
            "title": "Blade Runner",
            "director": "Ridley Scott",
            "year": 1982,
            "genre": "Sci-Fi",
        }
    )

    films = repository.list()

    assert [film.title for film in films] == ["Alien", "Blade Runner"]


def test_repository_updates_existing_film(session: Session) -> None:
    repository = FilmRepository(session)
    film = repository.create(
        {
            "title": "Alien",
            "director": "Ridley Scott",
            "year": 1979,
            "genre": "Sci-Fi",
        }
    )

    updated_film = repository.update(
        film,
        {
            "title": "Alien Director's Cut",
            "year": 2003,
        },
    )

    assert updated_film.title == "Alien Director's Cut"
    assert updated_film.year == 2003
    assert updated_film.director == "Ridley Scott"


def test_repository_deletes_existing_film(session: Session) -> None:
    repository = FilmRepository(session)
    film = repository.create(
        {
            "title": "Alien",
            "director": "Ridley Scott",
            "year": 1979,
            "genre": "Sci-Fi",
        }
    )

    repository.delete(film)

    assert repository.get_by_id(film.id) is None


def test_repository_returns_none_when_film_does_not_exist(session: Session) -> None:
    repository = FilmRepository(session)

    assert repository.get_by_id(999) is None
