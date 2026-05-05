"""C08 — W7 D4 F4.1 FastAPI exception handlers (uniform ApiError contract).

Maps HTTPException / RequestValidationError / generic Exception to the
`{"error": {"code", "message", "actionable_hint"}}` envelope. NO raw stack
traces escape: server-side error gets logged via structlog (F3 audit pipeline)
while the response carries a generic safe message.
"""

from __future__ import annotations

import structlog
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.schemas.errors import ApiErrorBody, ApiErrorResponse, ErrorCodes

_logger = structlog.get_logger("ekp.api.errors")


_STATUS_TO_CODE: dict[int, str] = {
    status.HTTP_401_UNAUTHORIZED: ErrorCodes.AUTH_UNAUTHORIZED,
    status.HTTP_403_FORBIDDEN: ErrorCodes.AUTH_FORBIDDEN,
    status.HTTP_404_NOT_FOUND: ErrorCodes.RESOURCE_NOT_FOUND,
    status.HTTP_409_CONFLICT: ErrorCodes.RESOURCE_CONFLICT,
    status.HTTP_429_TOO_MANY_REQUESTS: ErrorCodes.RATE_LIMIT_EXCEEDED,
    status.HTTP_502_BAD_GATEWAY: ErrorCodes.PIPELINE_RETRIEVAL_FAILED,
    status.HTTP_503_SERVICE_UNAVAILABLE: ErrorCodes.PIPELINE_SYNTHESIS_FAILED,
    status.HTTP_504_GATEWAY_TIMEOUT: ErrorCodes.PIPELINE_LLM_TIMEOUT,
}


_HINTS: dict[str, str] = {
    ErrorCodes.AUTH_UNAUTHORIZED: "Sign in again or refresh your session.",
    ErrorCodes.AUTH_FORBIDDEN: "Contact your KB owner for access.",
    ErrorCodes.RATE_LIMIT_EXCEEDED: "Wait a few seconds and retry — see Retry-After header.",
    ErrorCodes.VALIDATION_INVALID_PAYLOAD: "Check the request body shape and retry.",
    ErrorCodes.VALIDATION_QUERY_TOO_LONG: "Shorten the query (max 2000 characters).",
    ErrorCodes.RESOURCE_NOT_FOUND: "Verify the KB / document / chunk id and retry.",
    ErrorCodes.RESOURCE_CONFLICT: "The resource already exists or was modified.",
    ErrorCodes.PIPELINE_RETRIEVAL_FAILED: "The retrieval backend is degraded — retry shortly.",
    ErrorCodes.PIPELINE_SYNTHESIS_FAILED: "The answer-generation service is unavailable — retry shortly.",
    ErrorCodes.PIPELINE_LLM_TIMEOUT: "The model took too long — retry once.",
    ErrorCodes.PIPELINE_RERANKER_OUTAGE: "Reranker is degraded — results may be lower quality.",
    ErrorCodes.QUERY_NO_RELEVANT_CONTENT: "Try rephrasing or expanding your question.",
    ErrorCodes.INTERNAL_SERVER_ERROR: "Something went wrong — retry, and report if it persists.",
}


def _build_response(
    status_code: int,
    code: str,
    message: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body = ApiErrorResponse(
        error=ApiErrorBody(
            code=code,
            message=message,
            actionable_hint=_HINTS.get(code),
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(),
        headers=headers,
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    code = _STATUS_TO_CODE.get(exc.status_code, ErrorCodes.INTERNAL_SERVER_ERROR)
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return _build_response(
        status_code=exc.status_code,
        code=code,
        message=message,
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    # Pydantic raises with a list of error dicts; surface a digest message
    # without leaking raw input values back (CLAUDE.md §5.5 H5 redaction).
    first = exc.errors()[0] if exc.errors() else {}
    raw_type = str(first.get("type", ""))
    raw_msg = str(first.get("msg", "invalid payload"))
    message = "Request payload failed validation."
    code = ErrorCodes.VALIDATION_INVALID_PAYLOAD
    if raw_type == "string_too_long" or "at most" in raw_msg.lower() or "too long" in raw_msg.lower():
        code = ErrorCodes.VALIDATION_QUERY_TOO_LONG
        message = "Query exceeds maximum length (2000 characters)."
    return _build_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code=code,
        message=message,
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    # Server-side structured log — full type + repr for ops debugging.
    _logger.error(
        "unhandled_exception",
        exception_type=type(exc).__name__,
        exception_repr=repr(exc),
        path=request.url.path,
        method=request.method,
    )
    # Client-facing — generic safe message; never the exception detail.
    return _build_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code=ErrorCodes.INTERNAL_SERVER_ERROR,
        message="An unexpected error occurred.",
    )


def register_error_handlers(app: FastAPI) -> None:
    """Wire all handlers on the FastAPI app (called from `server.py`)."""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
