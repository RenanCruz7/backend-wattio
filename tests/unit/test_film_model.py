from app.models.film import Film


def test_film_model_has_expected_mapping() -> None:
    columns = Film.__table__.columns

    assert Film.__tablename__ == "films"
    assert list(columns.keys()) == [
        "id",
        "title",
        "director",
        "year",
        "genre",
        "created_at",
    ]
    assert columns["id"].primary_key is True
    assert columns["title"].nullable is False
    assert columns["director"].nullable is False
    assert columns["year"].nullable is False
    assert columns["genre"].nullable is False
    assert columns["created_at"].server_default is not None
