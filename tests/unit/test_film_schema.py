from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.film import Film
from app.schemas.film import FilmCreate, FilmResponse, FilmUpdate


def test_film_create_normalizes_text_fields() -> None:
    schema = FilmCreate(
        title="  Alien  ",
        director="  Ridley Scott  ",
        year=1979,
        genre="  Sci-Fi  ",
    )

    assert schema.model_dump() == {
        "title": "Alien",
        "director": "Ridley Scott",
        "year": 1979,
        "genre": "Sci-Fi",
    }


def test_film_update_allows_partial_payload() -> None:
    schema = FilmUpdate(title="  Blade Runner ")

    assert schema.model_dump(exclude_none=True) == {"title": "Blade Runner"}


def test_film_response_can_be_created_from_orm_object() -> None:
    film = Film(
        id=1,
        title="Alien",
        director="Ridley Scott",
        year=1979,
        genre="Sci-Fi",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
    )

    schema = FilmResponse.model_validate(film)

    assert schema.id == 1
    assert schema.title == "Alien"
    assert schema.created_at.tzinfo is not None


def test_film_create_rejects_blank_text_fields() -> None:
    with pytest.raises(ValidationError):
        FilmCreate(title="   ", director="Director", year=1999, genre="Drama")
