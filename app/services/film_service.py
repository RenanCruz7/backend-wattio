from app.models.film import Film
from app.repositories.film_repository import FilmRepository
from app.schemas.film import FilmCreate, FilmUpdate


class FilmNotFoundError(Exception):
    def __init__(self, film_id: int) -> None:
        self.film_id = film_id
        super().__init__(f"Film with id={film_id} was not found")


class FilmService:
    def __init__(self, repository: FilmRepository) -> None:
        self.repository = repository

    def list_films(self) -> list[Film]:
        return self.repository.list()

    def create_film(self, payload: FilmCreate) -> Film:
        return self.repository.create(payload.model_dump())

    def get_film_by_id(self, film_id: int) -> Film:
        film = self.repository.get_by_id(film_id)
        if film is None:
            raise FilmNotFoundError(film_id)
        return film

    def update_film(self, film_id: int, payload: FilmUpdate) -> Film:
        film = self.get_film_by_id(film_id)
        update_data = payload.model_dump(exclude_none=True)

        if not update_data:
            return film

        return self.repository.update(film, update_data)

    def delete_film(self, film_id: int) -> None:
        film = self.get_film_by_id(film_id)
        self.repository.delete(film)
