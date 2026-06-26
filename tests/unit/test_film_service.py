from datetime import datetime

import pytest

from app.models.film import Film
from app.schemas.film import FilmCreate, FilmUpdate
from app.services.film_service import FilmNotFoundError, FilmService


class FakeFilmRepository:
    def __init__(self) -> None:
        self.films: dict[int, Film] = {}
        self.next_id = 1

    def count(self) -> int:
        return len(self.films)

    def list(self, *, offset: int = 0, limit: int = 20) -> list[Film]:
        ordered_films = [self.films[film_id] for film_id in sorted(self.films)]
        return ordered_films[offset : offset + limit]

    def create(self, data: dict[str, object]) -> Film:
        film = Film(
            id=self.next_id,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            **data,
        )
        self.films[self.next_id] = film
        self.next_id += 1
        return film

    def get_by_id(self, film_id: int) -> Film | None:
        return self.films.get(film_id)

    def update(self, film: Film, data: dict[str, object]) -> Film:
        for field, value in data.items():
            setattr(film, field, value)
        return film

    def delete(self, film: Film) -> None:
        self.films.pop(film.id, None)


@pytest.fixture
def service() -> FilmService:
    return FilmService(FakeFilmRepository())


def test_service_creates_film(service: FilmService) -> None:
    film = service.create_film(
        FilmCreate(
            title="Alien",
            director="Ridley Scott",
            year=1979,
            genre="Sci-Fi",
        )
    )

    assert film.id == 1
    assert film.title == "Alien"


def test_service_replaces_existing_film(service: FilmService) -> None:
    created_film = service.create_film(
        FilmCreate(
            title="Alien",
            director="Ridley Scott",
            year=1979,
            genre="Sci-Fi",
        )
    )

    replaced_film = service.replace_film(
        created_film.id,
        FilmCreate(
            title="Blade Runner",
            director="Denis Villeneuve",
            year=2017,
            genre="Neo-Noir",
        ),
    )

    assert replaced_film.title == "Blade Runner"
    assert replaced_film.director == "Denis Villeneuve"
    assert replaced_film.year == 2017
    assert replaced_film.genre == "Neo-Noir"


def test_service_lists_films(service: FilmService) -> None:
    service.create_film(
        FilmCreate(
            title="Alien",
            director="Ridley Scott",
            year=1979,
            genre="Sci-Fi",
        )
    )
    service.create_film(
        FilmCreate(
            title="Blade Runner",
            director="Ridley Scott",
            year=1982,
            genre="Sci-Fi",
        )
    )

    films = service.list_films()

    assert [film.title for film in films.items] == ["Alien", "Blade Runner"]
    assert films.page == 1
    assert films.page_size == 20
    assert films.total_items == 2
    assert films.total_pages == 1


def test_service_lists_films_with_pagination(service: FilmService) -> None:
    service.create_film(
        FilmCreate(
            title="Alien",
            director="Ridley Scott",
            year=1979,
            genre="Sci-Fi",
        )
    )
    service.create_film(
        FilmCreate(
            title="Blade Runner",
            director="Ridley Scott",
            year=1982,
            genre="Sci-Fi",
        )
    )
    service.create_film(
        FilmCreate(
            title="The Martian",
            director="Ridley Scott",
            year=2015,
            genre="Sci-Fi",
        )
    )

    films = service.list_films(page=2, page_size=2)

    assert [film.title for film in films.items] == ["The Martian"]
    assert films.page == 2
    assert films.page_size == 2
    assert films.total_items == 3
    assert films.total_pages == 2


def test_service_returns_existing_film(service: FilmService) -> None:
    created_film = service.create_film(
        FilmCreate(
            title="Alien",
            director="Ridley Scott",
            year=1979,
            genre="Sci-Fi",
        )
    )

    film = service.get_film_by_id(created_film.id)

    assert film.id == created_film.id


def test_service_raises_for_missing_film(service: FilmService) -> None:
    with pytest.raises(FilmNotFoundError) as exc_info:
        service.get_film_by_id(999)

    assert exc_info.value.film_id == 999


def test_service_patches_existing_film(service: FilmService) -> None:
    created_film = service.create_film(
        FilmCreate(
            title="Alien",
            director="Ridley Scott",
            year=1979,
            genre="Sci-Fi",
        )
    )

    updated_film = service.patch_film(
        created_film.id,
        FilmUpdate(title="Alien Remastered", year=2003),
    )

    assert updated_film.title == "Alien Remastered"
    assert updated_film.year == 2003


def test_service_returns_existing_film_when_patch_payload_is_empty(
    service: FilmService,
) -> None:
    created_film = service.create_film(
        FilmCreate(
            title="Alien",
            director="Ridley Scott",
            year=1979,
            genre="Sci-Fi",
        )
    )

    same_film = service.patch_film(created_film.id, FilmUpdate())

    assert same_film.id == created_film.id
    assert same_film.title == "Alien"


def test_service_deletes_existing_film(service: FilmService) -> None:
    created_film = service.create_film(
        FilmCreate(
            title="Alien",
            director="Ridley Scott",
            year=1979,
            genre="Sci-Fi",
        )
    )

    service.delete_film(created_film.id)

    with pytest.raises(FilmNotFoundError):
        service.get_film_by_id(created_film.id)
