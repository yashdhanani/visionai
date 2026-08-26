from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError
from app.core.logging import logger, request_id_ctx


def _envelope(success: bool, payload: dict, request_id: str, status: int) -> JSONResponse:
    body = {"success": success, **payload, "meta": {"request_id": request_id}}
    return JSONResponse(body, status_code=status)


def install_exception_handlers(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        request_id_ctx.set(rid)
        request.state.request_id = rid
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("unhandled error", extra={"endpoint": request.url.path})
            raise
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = rid
        response.headers["X-Processing-Time-Ms"] = str(elapsed_ms)
        logger.info(
            "request",
            extra={
                "endpoint": request.url.path,
                "status": response.status_code,
                "processing_time_ms": elapsed_ms,
            },
        )
        return response

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return _envelope(
            False,
            {"error": {"code": exc.code, "message": exc.message}},
            getattr(request.state, "request_id", "-"),
            exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        first = errors[0] if errors else {}
        loc = ".".join(str(p) for p in first.get("loc", []) if p != "body")
        msg = f"{loc}: {first.get('msg', 'Invalid input')}" if loc else "Invalid request payload"
        return _envelope(
            False,
            {"error": {"code": "VALIDATION_ERROR", "message": msg, "details": errors}},
            getattr(request.state, "request_id", "-"),
            422,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException):
        code = {401: "UNAUTHORIZED", 403: "FORBIDDEN", 404: "NOT_FOUND"}.get(exc.status_code, "HTTP_ERROR")
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return _envelope(
            False,
            {"error": {"code": code, "message": detail}},
            getattr(request.state, "request_id", "-"),
            exc.status_code,
        )

    @app.exception_handler(SQLAlchemyError)
    async def db_error_handler(request: Request, exc: SQLAlchemyError):
        logging.getLogger("visionai.db").exception("database error")
        return _envelope(
            False,
            {"error": {"code": "DATABASE_ERROR", "message": "A database error occurred"}},
            getattr(request.state, "request_id", "-"),
            500,
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        logging.getLogger("visionai").exception("unhandled exception")
        return _envelope(
            False,
            {"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}},
            getattr(request.state, "request_id", "-"),
            500,
        )
