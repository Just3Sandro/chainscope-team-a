import logging
from http import HTTPStatus
from uuid import UUID

import pytest
from fastapi import Request
from pydantic import BaseModel

from app.core.errors import AppError, ErrorCode
from app.core.logging import request_id_context

EXPECTED_ERRORS = [
    (400, ErrorCode.VALIDATION_ERROR),
    (400, ErrorCode.INVALID_REFERENCE),
    (401, ErrorCode.UNAUTHENTICATED),
    (403, ErrorCode.FORBIDDEN),
    (404, ErrorCode.NOT_FOUND),
    (409, ErrorCode.CONFLICT),
    (413, ErrorCode.PAYLOAD_TOO_LARGE),
    (422, ErrorCode.VALIDATION_ERROR),
    (429, ErrorCode.RATE_LIMITED),
]
SECRET_INPUT = "fictional-private-value"


def assert_error(response, status, code):
    assert response.status_code == status
    error = response.json()["error"]
    assert set(error) == {"code", "message", "request_id"}
    assert error["code"] == code
    assert error["request_id"] == response.headers["X-Request-ID"]
    assert UUID(error["request_id"]).version == 4


def test_unknown_route(client):
    assert_error(client.get("/api/v1/unknown"), 404, ErrorCode.NOT_FOUND)


def test_method_not_allowed(client):
    response = client.post("/api/v1/health")
    assert_error(response, 405, ErrorCode.METHOD_NOT_ALLOWED)
    assert response.headers["allow"] == "GET"


class TestPayload(BaseModel):
    __test__ = False
    count: int


def test_validation_does_not_echo_input(application, client):
    @application.post("/test-validation")
    def validate(payload: TestPayload):
        return payload

    response = client.post("/test-validation", json={"count": SECRET_INPUT})
    assert_error(response, 422, ErrorCode.VALIDATION_ERROR)
    assert SECRET_INPUT not in response.text
    assert "input" not in response.json()["error"]


@pytest.mark.parametrize(("status", "code"), EXPECTED_ERRORS)
def test_app_errors(application, client, status, code):
    @application.get("/test-error")
    def fail():
        raise AppError(status, code, "Controlled error.")

    assert_error(client.get("/test-error"), status, code)


def test_unhandled_error(application, client, caplog):
    @application.get("/test-crash")
    def crash():
        raise RuntimeError(SECRET_INPUT)

    with caplog.at_level(logging.ERROR):
        response = client.get("/test-crash")
    assert_error(response, HTTPStatus.INTERNAL_SERVER_ERROR, ErrorCode.INTERNAL_ERROR)
    assert response.json()["error"]["message"] == "An internal error occurred."
    assert SECRET_INPUT not in response.text
    assert "Traceback" not in response.text
    assert SECRET_INPUT not in caplog.text
    assert "Unhandled RuntimeError" in caplog.text


def test_context_matches_request_state(application, client):
    @application.get("/test-context")
    async def context(request: Request):
        assert request_id_context.get() == request.state.request_id
        return {"request_id": request.state.request_id}

    first = client.get("/test-context")
    second = client.get("/test-context")
    assert first.json()["request_id"] == first.headers["X-Request-ID"]
    assert first.headers["X-Request-ID"] != second.headers["X-Request-ID"]
    assert request_id_context.get() is None
