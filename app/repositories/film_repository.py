from collections.abc import Mapping
from typing import Any, Literal

from sqlalchemy import Select, desc, func, select
from sqlalchemy.orm import Session

from app.models.film import Film

SortableFilmField = Literal["created_at", "title", "year"]
SortOrder = Literal["asc", "desc"]


class FilmRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _filter_clauses(
        self,
        *,
        title: str | None = None,
        genre: str | None = None,
        year: int | None = None,
    ) -> list[object]:
        clauses: list[object] = []

        if title:
            clauses.append(Film.title.ilike(f"%{title}%"))
        if genre:
            clauses.append(Film.genre.ilike(f"%{genre}%"))
        if year is not None:
            clauses.append(Film.year == year)

        return clauses

    def _apply_filters(
        self,
        statement: Select[tuple[Film]],
        *,
        title: str | None = None,
        genre: str | None = None,
        year: int | None = None,
    ) -> Select[tuple[Film]]:
        for clause in self._filter_clauses(title=title, genre=genre, year=year):
            statement = statement.where(clause)
        return statement

    def _apply_sort(
        self,
        statement: Select[tuple[Film]],
        *,
        sort_by: SortableFilmField,
        sort_order: SortOrder,
    ) -> Select[tuple[Film]]:
        sort_columns = {
            "created_at": (Film.created_at, Film.id),
            "title": (Film.title, Film.id),
            "year": (Film.year, Film.id),
        }
        ordered_columns = sort_columns[sort_by]

        if sort_order == "desc":
            return statement.order_by(*(desc(column) for column in ordered_columns))

        return statement.order_by(*ordered_columns)

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        title: str | None = None,
        genre: str | None = None,
        year: int | None = None,
        sort_by: SortableFilmField = "created_at",
        sort_order: SortOrder = "asc",
    ) -> list[Film]:
        statement = select(Film)
        statement = self._apply_filters(statement, title=title, genre=genre, year=year)
        statement = self._apply_sort(statement, sort_by=sort_by, sort_order=sort_order)
        statement = statement.offset(offset).limit(limit)
        return list(self.session.scalars(statement))

    def count(
        self,
        *,
        title: str | None = None,
        genre: str | None = None,
        year: int | None = None,
    ) -> int:
        statement = select(func.count()).select_from(Film)
        for clause in self._filter_clauses(title=title, genre=genre, year=year):
            statement = statement.where(clause)
        return self.session.scalar(statement) or 0

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

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
