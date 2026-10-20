"""Consistent JSON error responses: {"error": {"code": ..., "message": ..., "details": ...}}."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("krishiveda")


class AppError(Exception):
    """Raise this from services/routes for expected, user-facing errors."""

    def __init__(self, status_code: int, code: str, message: str, details: dict | None = None):
        self.status_code, self.code, self.message, self.details = status_code, code, message, details
        super().__init__(message)


def _body(code: str, message: str, details=None) -> dict:
    err = {"code": code, "message": message}
    if details:
        err["details"] = details
    return {"error": err}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error(_: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content=_body(exc.code, exc.message, exc.details))

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        fields = [
            {"field": ".".join(str(p) for p in e["loc"] if p != "body"), "message": e["msg"]}
            for e in exc.errors()
        ]
        return JSONResponse(status_code=422, content=_body("VALIDATION_ERROR", "Some inputs are invalid.", {"fields": fields}))

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException):
        code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(exc.status_code, "HTTP_ERROR")
        return JSONResponse(status_code=exc.status_code, content=_body(code, str(exc.detail)))

    @app.exception_handler(Exception)
    async def unhandled(_: Request, exc: Exception):
        # Log the real error for developers, but never leak internals to the client.
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(status_code=500, content=_body("INTERNAL_ERROR", "Something went wrong. Please try again."))
