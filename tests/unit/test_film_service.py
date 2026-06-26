from datetime import datetime

import pytest

from app.models.film import Film
from app.schemas.film import FilmCreate, FilmUpdate
from app.services.film_service import FilmNotFoundError, FilmService


class FakeFilmRepository:
    def __init__(self) -> None:
        self.films: dict[int, Film] = {}
        self.next_id = 1
        self.commit_calls = 0
        self.rollback_calls = 0

    def count(self, *, title: str | None = None, genre: str | None = None, year: int | None = None) -> int:
        return len(self.list(title=title, genre=genre, year=year, limit=10_000))

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        title: str | None = None,
        genre: str | None = None,
        year: int | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[Film]:
        ordered_films = [self.films[film_id] for film_id in sorted(self.films)]

        if title:
            ordered_films = [film for film in ordered_films if title.lower() in film.title.lower()]
        if genre:
            ordered_films = [film for film in ordered_films if genre.lower() in film.genre.lower()]
        if year is not None:
            ordered_films = [film for film in ordered_films if film.year == year]

        ordered_films.sort(key=lambda film: getattr(film, sort_by))
        if sort_order == "desc":
            ordered_films.reverse()

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

    def commit(self) -> None:
        self.commit_calls += 1

    def rollback(self) -> None:
        self.rollback_calls += 1


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
    assert service.repository.commit_calls == 1


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
    assert service.repository.commit_calls == 2


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


def test_service_lists_films_with_filters_and_sorting(service: FilmService) -> None:
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
            title="Gladiator",
            director="Ridley Scott",
            year=2000,
            genre="Drama",
        )
    )

    films = service.list_films(title="e", genre="sci", sort_by="year", sort_order="asc")

    assert [film.title for film in films.items] == ["Alien", "Blade Runner"]
    assert films.total_items == 2


def test_service_lists_empty_collection_with_zero_total_pages(service: FilmService) -> None:
    films = service.list_films()

    assert films.items == []
    assert films.total_items == 0
    assert films.total_pages == 0


def test_service_returns_empty_items_when_page_exceeds_total_pages(service: FilmService) -> None:
    service.create_film(
        FilmCreate(
            title="Alien",
            director="Ridley Scott",
            year=1979,
            genre="Sci-Fi",
        )
    )

    films = service.list_films(page=2, page_size=1)

    assert films.items == []
    assert films.total_items == 1
    assert films.total_pages == 1


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
    assert service.repository.commit_calls == 2


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
    assert service.repository.commit_calls == 1


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
    assert service.repository.commit_calls == 2

    with pytest.raises(FilmNotFoundError):
        service.get_film_by_id(created_film.id)
