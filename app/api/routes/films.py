from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.film_repository import FilmRepository
from app.schemas.common import ErrorResponse, ValidationErrorResponse
from app.schemas.film import FilmCreate, FilmListResponse, FilmResponse, FilmUpdate
from app.services.film_service import FilmService

router = APIRouter(prefix="/filmes")

DbSession = Annotated[Session, Depends(get_db)]


def get_film_service(session: DbSession) -> FilmService:
    repository = FilmRepository(session)
    return FilmService(repository)


FilmServiceDependency = Annotated[FilmService, Depends(get_film_service)]

NOT_FOUND_RESPONSE = {
    "model": ErrorResponse,
    "description": "Filme nao encontrado para o identificador informado.",
}

VALIDATION_ERROR_RESPONSE = {
    "model": ValidationErrorResponse,
    "description": "Payload ou parametros de consulta invalidos.",
}

INTEGRITY_ERROR_RESPONSE = {
    "model": ErrorResponse,
    "description": "Conflito de integridade ao persistir os dados.",
}

DATABASE_UNAVAILABLE_RESPONSE = {
    "model": ErrorResponse,
    "description": "Banco de dados indisponivel para atender a operacao.",
}

DATABASE_ERROR_RESPONSE = {
    "model": ErrorResponse,
    "description": "Falha inesperada ao executar operacao no banco de dados.",
}


@router.get(
    "",
    response_model=FilmListResponse,
    summary="Listar filmes",
    description=(
        "Retorna a lista paginada de filmes cadastrados. "
        "Use `page` e `page_size` para navegar pelos resultados. "
        "Quando nao houver registros, `total_pages` sera `0`. "
        "Quando a pagina solicitada ultrapassar a ultima pagina disponivel, `items` sera retornado vazio."
    ),
    response_description="Pagina atual de filmes cadastrados.",
    responses={422: VALIDATION_ERROR_RESPONSE, 503: DATABASE_UNAVAILABLE_RESPONSE, 500: DATABASE_ERROR_RESPONSE},
)
def list_films(
    service: FilmServiceDependency,
    page: int = Query(
        default=1,
        ge=1,
        description="Numero da pagina a partir de 1.",
        examples=[1],
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Quantidade maxima de itens por pagina.",
        examples=[20],
    ),
    title: str | None = Query(
        default=None,
        min_length=1,
        description="Filtra filmes por titulo com busca parcial case-insensitive.",
    ),
    genre: str | None = Query(
        default=None,
        min_length=1,
        description="Filtra filmes por genero com busca parcial case-insensitive.",
    ),
    year: int | None = Query(
        default=None,
        ge=1888,
        le=2100,
        description="Filtra filmes por ano exato.",
    ),
    sort_by: Literal["created_at", "title", "year"] = Query(
        default="created_at",
        description="Campo utilizado para ordenacao.",
    ),
    sort_order: Literal["asc", "desc"] = Query(
        default="asc",
        description="Direcao da ordenacao.",
    ),
) -> FilmListResponse:
    paginated_films = service.list_films(
        page=page,
        page_size=page_size,
        title=title,
        genre=genre,
        year=year,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return FilmListResponse(
        items=[FilmResponse.model_validate(film) for film in paginated_films.items],
        page=paginated_films.page,
        page_size=paginated_films.page_size,
        total_items=paginated_films.total_items,
        total_pages=paginated_films.total_pages,
    )


@router.post(
    "",
    response_model=FilmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar filme",
    description="Cria um novo filme com os dados informados no corpo da requisicao.",
    response_description="Filme criado com sucesso.",
    responses={409: INTEGRITY_ERROR_RESPONSE, 422: VALIDATION_ERROR_RESPONSE, 503: DATABASE_UNAVAILABLE_RESPONSE, 500: DATABASE_ERROR_RESPONSE},
)
def create_film(
    payload: FilmCreate,
    service: FilmServiceDependency,
) -> FilmResponse:
    film = service.create_film(payload)
    return FilmResponse.model_validate(film)


@router.get(
    "/{film_id}",
    response_model=FilmResponse,
    summary="Buscar filme por id",
    description="Retorna os dados de um filme especifico pelo identificador informado.",
    response_description="Filme encontrado.",
    responses={404: NOT_FOUND_RESPONSE, 422: VALIDATION_ERROR_RESPONSE, 503: DATABASE_UNAVAILABLE_RESPONSE, 500: DATABASE_ERROR_RESPONSE},
)
def get_film(film_id: int, service: FilmServiceDependency) -> FilmResponse:
    film = service.get_film_by_id(film_id)
    return FilmResponse.model_validate(film)


@router.put(
    "/{film_id}",
    response_model=FilmResponse,
    summary="Substituir filme",
    description=(
        "Substitui integralmente um filme existente. "
        "Todos os campos obrigatorios devem ser enviados."
    ),
    response_description="Filme substituido com sucesso.",
    responses={404: NOT_FOUND_RESPONSE, 409: INTEGRITY_ERROR_RESPONSE, 422: VALIDATION_ERROR_RESPONSE, 503: DATABASE_UNAVAILABLE_RESPONSE, 500: DATABASE_ERROR_RESPONSE},
)
def replace_film(
    film_id: int,
    payload: FilmCreate,
    service: FilmServiceDependency,
) -> FilmResponse:
    film = service.replace_film(film_id, payload)
    return FilmResponse.model_validate(film)


@router.patch(
    "/{film_id}",
    response_model=FilmResponse,
    summary="Atualizar filme parcialmente",
    description="Atualiza apenas os campos enviados para um filme existente.",
    response_description="Filme atualizado parcialmente com sucesso.",
    responses={404: NOT_FOUND_RESPONSE, 409: INTEGRITY_ERROR_RESPONSE, 422: VALIDATION_ERROR_RESPONSE, 503: DATABASE_UNAVAILABLE_RESPONSE, 500: DATABASE_ERROR_RESPONSE},
)
def patch_film(
    film_id: int,
    payload: FilmUpdate,
    service: FilmServiceDependency,
) -> FilmResponse:
    film = service.patch_film(film_id, payload)
    return FilmResponse.model_validate(film)


@router.delete(
    "/{film_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover filme",
    description="Remove permanentemente um filme existente.",
    response_description="Filme removido com sucesso.",
    responses={404: NOT_FOUND_RESPONSE, 503: DATABASE_UNAVAILABLE_RESPONSE, 500: DATABASE_ERROR_RESPONSE},
)
def delete_film(film_id: int, service: FilmServiceDependency) -> Response:
    service.delete_film(film_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
