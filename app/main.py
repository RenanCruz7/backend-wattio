from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.db.session import dispose_engine
from app.services.film_service import FilmNotFoundError


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "API REST para gerenciamento de filmes com CRUD completo, "
            "paginacao, persistencia em PostgreSQL e migrations com Alembic."
        ),
        lifespan=lifespan,
    )

    async def film_not_found_exception_handler(
        _: Request,
        exc: FilmNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": f"Filme com id {exc.film_id} nao encontrado"},
        )

    application.add_exception_handler(
        FilmNotFoundError,
        film_not_found_exception_handler,
    )
    application.include_router(api_router)
    return application


app = create_app()
