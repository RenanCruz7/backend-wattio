from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str


class ValidationErrorItem(BaseModel):
    type: str
    loc: list[str | int]
    msg: str
    input: object | None = None


class ValidationErrorResponse(BaseModel):
    detail: list[ValidationErrorItem]
