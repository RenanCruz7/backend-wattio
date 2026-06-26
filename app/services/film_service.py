from dataclasses import dataclass

from app.models.film import Film
from app.repositories.film_repository import FilmRepository, SortOrder, SortableFilmField
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

    def list_films(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        title: str | None = None,
        genre: str | None = None,
        year: int | None = None,
        sort_by: SortableFilmField = "created_at",
        sort_order: SortOrder = "asc",
    ) -> PaginatedFilms:
        total_items = self.repository.count(title=title, genre=genre, year=year)
        offset = (page - 1) * page_size
        items = self.repository.list(
            offset=offset,
            limit=page_size,
            title=title,
            genre=genre,
            year=year,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        total_pages = (total_items + page_size - 1) // page_size if total_items else 0

        return PaginatedFilms(
            items=items,
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )

    def create_film(self, payload: FilmCreate) -> Film:
        try:
            film = self.repository.create(payload.model_dump())
            self.repository.commit()
            return film
        except Exception:
            self.repository.rollback()
            raise

    def replace_film(self, film_id: int, payload: FilmCreate) -> Film:
        film = self.get_film_by_id(film_id)
        try:
            replaced_film = self.repository.update(film, payload.model_dump())
            self.repository.commit()
            return replaced_film
        except Exception:
            self.repository.rollback()
            raise

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

        try:
            updated_film = self.repository.update(film, update_data)
            self.repository.commit()
            return updated_film
        except Exception:
            self.repository.rollback()
            raise

    def delete_film(self, film_id: int) -> None:
        film = self.get_film_by_id(film_id)
        try:
            self.repository.delete(film)
            self.repository.commit()
        except Exception:
            self.repository.rollback()
            raise
