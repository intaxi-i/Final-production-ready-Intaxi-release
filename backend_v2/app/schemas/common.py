from __future__ import annotations

from pydantic import BaseModel


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: dict = {}


class ErrorResponse(BaseModel):
    error: ErrorPayload


class PageMeta(BaseModel):
    limit: int = 50
    offset: int = 0
    total: int | None = None
