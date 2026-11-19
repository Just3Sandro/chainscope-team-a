import logging
import traceback
from enum import StrEnum
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.core.logging import request_id_context
from app.core.middleware import REQUEST_ID_HEADER

logger = logging.getLogger(__name__)


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_REFERENCE = "INVALID_REFERENCE"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    CONFLICT = "CONFLICT"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


STATUS_CODES = {
    HTTPStatus.BAD_REQUEST: ErrorCode.VALIDATION_ERROR,
    HTTPStatus.UNAUTHORIZED: ErrorCode.UNAUTHENTICATED,
    HTTPStatus.FORBIDDEN: ErrorCode.FORBIDDEN,
    HTTPStatus.NOT_FOUND: ErrorCode.NOT_FOUND,
    HTTPStatus.METHOD_NOT_ALLOWED: ErrorCode.METHOD_NOT_ALLOWED,
    HTTPStatus.CONFLICT: ErrorCode.CONFLICT,
    HTTPStatus.REQUEST_ENTITY_TOO_LARGE: ErrorCode.PAYLOAD_TOO_LARGE,
    HTTPStatus.UNPROCESSABLE_ENTITY: ErrorCode.VALIDATION_ERROR,
    HTTPStatus.TOO_MANY_REQUESTS: ErrorCode.RATE_LIMITED,
    HTTPStatus.INTERNAL_SERVER_ERROR: ErrorCode.INTERNAL_ERROR,
}
INTERNAL_ERROR_MESSAGE = "An internal error occurred."
VALIDATION_ERROR_MESSAGE = "Request validation failed."


class AppError(Exception):
    def __init__(self, status_code: int, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def error_response(
    request: Request, status_code: int, code: ErrorCode, message: str
) -> JSONResponse:
    # ServerErrorMiddleware runs after the request context has been reset.
    request_id = request_id_context.get() or request.state.request_id
    return make_error_response(request_id, status_code, code, message)


def make_error_response(
    request_id: str, status_code: int, code: ErrorCode, message: str
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "request_id": request_id}},
        headers={REQUEST_ID_HEADER: request_id},
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return error_response(request, exc.status_code, exc.code, exc.message)


async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code = STATUS_CODES.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
    message = (
        INTERNAL_ERROR_MESSAGE
        if exc.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR
        else HTTPStatus(exc.status_code).phrase
    )
    response = error_response(request, exc.status_code, code, message)
    if exc.headers:
        response.headers.update(exc.headers)
    response.headers[REQUEST_ID_HEADER] = request.state.request_id
    return response


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return error_response(
        request,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        ErrorCode.VALIDATION_ERROR,
        VALIDATION_ERROR_MESSAGE,
    )


async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    token = request_id_context.set(request.state.request_id)
    try:
        # Exception messages may contain submitted values; log only the type/frames.
        logger.error(
            "Unhandled %s frames=%s",
            type(exc).__name__,
            [
                (frame.filename.rsplit("/", 1)[-1], frame.name, frame.lineno)
                for frame in traceback.extract_tb(exc.__traceback__)
            ],
        )
        return error_response(
            request,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            ErrorCode.INTERNAL_ERROR,
            INTERNAL_ERROR_MESSAGE,
        )
    finally:
        request_id_context.reset(token)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, internal_error_handler)
