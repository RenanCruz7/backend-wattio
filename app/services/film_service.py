from dataclasses import dataclass

from app.models.film import Film
from app.repositories.film_repository import FilmRepository
from app.schemas.film import FilmCreate, FilmUpdate


class FilmNotFoundError(Exception):
    def __init__(self, film_id: int) -> None:
        self.film_id = film_id
        super().__init__(f"Film with id={film_id} was not found")


@dataclass(slots=True)
class PaginatedFilms:
    items: list[Film]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class FilmService:
    def __init__(self, repository: FilmRepository) -> None:
        self.repository = repository

    def list_films(self, *, page: int = 1, page_size: int = 20) -> PaginatedFilms:
        total_items = self.repository.count()
        offset = (page - 1) * page_size
        items = self.repository.list(offset=offset, limit=page_size)
        total_pages = (total_items + page_size - 1) // page_size if total_items else 0

        return PaginatedFilms(
            items=items,
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )

    def create_film(self, payload: FilmCreate) -> Film:
        return self.repository.create(payload.model_dump())

    def replace_film(self, film_id: int, payload: FilmCreate) -> Film:
        film = self.get_film_by_id(film_id)
        return self.repository.update(film, payload.model_dump())

    def get_film_by_id(self, film_id: int) -> Film:
        film = self.repository.get_by_id(film_id)
        if film is None:
            raise FilmNotFoundError(film_id)
        return film

    def patch_film(self, film_id: int, payload: FilmUpdate) -> Film:
        film = self.get_film_by_id(film_id)
        update_data = payload.model_dump(exclude_none=True)

        if not update_data:
            return film

        return self.repository.update(film, update_data)

    def delete_film(self, film_id: int) -> None:
        film = self.get_film_by_id(film_id)
        self.repository.delete(film)
