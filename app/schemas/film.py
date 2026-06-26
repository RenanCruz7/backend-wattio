from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FilmBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    director: str = Field(min_length=1, max_length=255)
    year: int = Field(ge=1888, le=2100)
    genre: str = Field(min_length=1, max_length=100)

    @field_validator("title", "director", "genre")
    @classmethod
    def strip_and_validate_text(cls, value: str) -> str:
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("must not be blank")
        return normalized_value


class FilmCreate(FilmBase):
    pass


class FilmUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    director: str | None = Field(default=None, min_length=1, max_length=255)
    year: int | None = Field(default=None, ge=1888, le=2100)
    genre: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("title", "director", "genre")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value

        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("must not be blank")
        return normalized_value


class FilmResponse(FilmBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def ensure_created_at_has_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value


class FilmListResponse(BaseModel):
    items: list[FilmResponse]
    page: int
    page_size: int
    total_items: int
    total_pages: int
