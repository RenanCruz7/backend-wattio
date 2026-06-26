from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.core.config import get_settings
from app.db.session import is_database_available
from app.schemas.health import HealthChecksResponse, HealthResponse

router = APIRouter()


def database_health_check() -> bool:
    return is_database_available()


DatabaseHealthStatus = Annotated[bool, Depends(database_health_check)]


def build_health_response(*, database_available: bool | None = None) -> HealthResponse:
    settings = get_settings()

    if database_available is None:
        return HealthResponse(
            status="ok",
            app=settings.app_name,
            version=settings.app_version,
        )

    return HealthResponse(
        status="ok" if database_available else "degraded",
        app=settings.app_name,
        version=settings.app_version,
        checks=HealthChecksResponse(
            database="ok" if database_available else "unavailable",
        ),
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Consultar status da aplicacao",
    description=(
        "Retorna a visao agregada da aplicacao, incluindo o estado do banco de dados. "
        "Pode responder `503` quando a API estiver viva, mas ainda nao pronta para atender."
    ),
    response_description="Estado agregado da aplicacao.",
    responses={
        503: {
            "model": HealthResponse,
            "description": "Aplicacao viva, mas banco indisponivel.",
        }
    },
)
def healthcheck(
    response: Response,
    database_available: DatabaseHealthStatus,
) -> HealthResponse:
    if not database_available:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return build_health_response(database_available=database_available)


@router.get(
    "/health/live",
    response_model=HealthResponse,
    summary="Consultar liveness",
    description="Indica se o processo da API esta vivo e respondendo requisicoes.",
    response_description="Processo da aplicacao ativo.",
)
def liveness() -> HealthResponse:
    return build_health_response()


@router.get(
    "/health/ready",
    response_model=HealthResponse,
    summary="Consultar readiness",
    description="Verifica se a API esta pronta para atender, incluindo conectividade com o banco.",
    response_description="Aplicacao pronta para atender requisicoes de negocio.",
    responses={
        503: {
            "model": HealthResponse,
            "description": "Aplicacao viva, mas ainda nao pronta por indisponibilidade do banco.",
        }
    },
)
def readiness(
    response: Response,
    database_available: DatabaseHealthStatus,
) -> HealthResponse:
    if not database_available:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return build_health_response(database_available=database_available)
