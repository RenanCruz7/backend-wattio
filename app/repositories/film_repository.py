from collections.abc import Mapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.film import Film


class FilmRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> list[Film]:
        statement = select(Film).order_by(Film.id)
        return list(self.session.scalars(statement))

    def create(self, data: Mapping[str, Any]) -> Film:
        film = Film(**dict(data))
        self.session.add(film)
        self.session.flush()
        self.session.refresh(film)
        return film

    def get_by_id(self, film_id: int) -> Film | None:
        return self.session.get(Film, film_id)

    def update(self, film: Film, data: Mapping[str, Any]) -> Film:
        for field, value in data.items():
            setattr(film, field, value)

        self.session.add(film)
        self.session.flush()
        self.session.refresh(film)
        return film

    def delete(self, film: Film) -> None:
        self.session.delete(film)
        self.session.flush()
