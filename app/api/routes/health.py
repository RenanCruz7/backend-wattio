from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Consultar status da aplicacao",
    description="Retorna o status basico da API e os metadados da aplicacao.",
    response_description="Aplicacao respondendo normalmente.",
)
def healthcheck() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.app_version,
    )
