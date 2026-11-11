"""
Exceções padronizadas e handlers globais para o FastAPI.
Garante respostas de erro consistentes e rastreáveis.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class NexoException(HTTPException):
    """Exceção de negócio padronizada do Projeto Nexo."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = "NEXO_ERROR",
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.extra = extra or {}


async def nexo_exception_handler(request: Request, exc: NexoException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "ok": False,
            "error_code": exc.error_code,
            "message": exc.detail,
            "detail": exc.detail,
            "request_id": request_id,
            **exc.extra,
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    errors = []
    for err in exc.errors():
        loc = ".".join(str(x) for x in err.get("loc", []) if x != "body")
        errors.append({"field": loc, "message": err.get("msg", "Valor inválido.")})
    first_msg = errors[0]["message"] if errors else "Dados de entrada inválidos."
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "ok": False,
            "error_code": "VALIDATION_ERROR",
            "message": first_msg,
            "detail": first_msg,
            "errors": errors,
            "request_id": request_id,
        },
    )
