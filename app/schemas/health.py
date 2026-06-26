from pydantic import BaseModel


class HealthChecksResponse(BaseModel):
    database: str | None = None


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    checks: HealthChecksResponse | None = None
