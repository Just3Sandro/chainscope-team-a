from http import HTTPStatus

from starlette.datastructures import Headers
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response

from app.core.errors import ErrorCode, make_error_response
from app.core.logging import request_id_context


class NormalizedCORSMiddleware(CORSMiddleware):
    def preflight_response(self, request_headers: Headers) -> Response:
        response = super().preflight_response(request_headers)
        if response.status_code != HTTPStatus.BAD_REQUEST:
            return response
        request_id = request_id_context.get()
        if request_id is None:
            raise RuntimeError("CORS requires the request ID middleware")
        normalized = make_error_response(
            request_id,
            HTTPStatus.BAD_REQUEST,
            ErrorCode.VALIDATION_ERROR,
            "CORS preflight rejected.",
        )
        for key, value in response.headers.items():
            if key.lower() not in {"content-type", "content-length"}:
                normalized.headers[key] = value
        return normalized
