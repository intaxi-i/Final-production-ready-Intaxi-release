from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, status


@dataclass(slots=True)
class ErrorCode:
    code: str
    message: str
    http_status: int = status.HTTP_400_BAD_REQUEST


class DomainError(Exception):
    def __init__(self, code: str, message: str, http_status: int = 400, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status
        self.details = details or {}

    def to_http(self) -> HTTPException:
        return HTTPException(
            status_code=self.http_status,
            detail={"error": {"code": self.code, "message": self.message, "details": self.details}},
        )


def raise_domain(code: str, message: str, http_status: int = 400, **details: Any) -> None:
    raise DomainError(code=code, message=message, http_status=http_status, details=details)
