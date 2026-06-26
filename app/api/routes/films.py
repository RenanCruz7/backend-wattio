from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.film_repository import FilmRepository
from app.schemas.film import FilmCreate, FilmResponse, FilmUpdate
from app.services.film_service import FilmNotFoundError, FilmService

router = APIRouter(prefix="/filmes")

DbSession = Annotated[Session, Depends(get_db)]


def get_film_service(session: DbSession) -> FilmService:
    repository = FilmRepository(session)
    return FilmService(repository)


FilmServiceDependency = Annotated[FilmService, Depends(get_film_service)]


@router.get("", response_model=list[FilmResponse])
def list_films(service: FilmServiceDependency) -> list[FilmResponse]:
    return [FilmResponse.model_validate(film) for film in service.list_films()]


@router.post("", response_model=FilmResponse, status_code=status.HTTP_201_CREATED)
def create_film(
    payload: FilmCreate,
    service: FilmServiceDependency,
) -> FilmResponse:
    film = service.create_film(payload)
    return FilmResponse.model_validate(film)


@router.get("/{film_id}", response_model=FilmResponse)
def get_film(film_id: int, service: FilmServiceDependency) -> FilmResponse:
    try:
        film = service.get_film_by_id(film_id)
    except FilmNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Filme com id {exc.film_id} nao encontrado",
        ) from exc

    return FilmResponse.model_validate(film)


@router.put("/{film_id}", response_model=FilmResponse)
def update_film(
    film_id: int,
    payload: FilmUpdate,
    service: FilmServiceDependency,
) -> FilmResponse:
    try:
        film = service.update_film(film_id, payload)
    except FilmNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Filme com id {exc.film_id} nao encontrado",
        ) from exc

    return FilmResponse.model_validate(film)


@router.delete("/{film_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_film(film_id: int, service: FilmServiceDependency) -> Response:
    try:
        service.delete_film(film_id)
    except FilmNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Filme com id {exc.film_id} nao encontrado",
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
