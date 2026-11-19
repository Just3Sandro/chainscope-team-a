import logging
from http import HTTPStatus

import pytest

from app.core.logging import RequestIdFilter, request_id_context

ACCESS_LOGGER = "app.core.middleware"
SENSITIVE_VALUES = (
    "fictif-invitation-123",
    "token=",
    "fictif-cookie",
    "fictif-csrf",
)


@pytest.mark.parametrize(
    ("path", "status"),
    [
        ("/api/v1/health", HTTPStatus.OK),
        ("/api/v1/unknown", HTTPStatus.NOT_FOUND),
        ("/test-crash", HTTPStatus.INTERNAL_SERVER_ERROR),
    ],
)
def test_access_log_excludes_sensitive_values(
    application, client, caplog, path, status
):
    @application.get("/test-crash")
    async def crash():
        raise RuntimeError(SENSITIVE_VALUES[0])

    # Capture server logs, excluding HTTPX's client-side request diagnostics.
    caplog.set_level(logging.WARNING)
    caplog.set_level(logging.INFO, logger=ACCESS_LOGGER)
    # Pytest's capture handler needs the same filter as the server's handler.
    caplog.handler.addFilter(RequestIdFilter())
    response = client.get(
        f"{path}?token={SENSITIVE_VALUES[0]}",
        headers={"Cookie": "session=fictif-cookie", "X-CSRF-Token": "fictif-csrf"},
    )

    assert response.status_code == status
    access_records = [
        record for record in caplog.records if record.name == ACCESS_LOGGER
    ]
    assert len(access_records) == 1
    record = access_records[0]
    assert record.getMessage() == f"HTTP GET {path} status={status.value}"
    assert record.request_id == response.headers["X-Request-ID"]
    assert record.request_id != "-"
    assert all(value not in caplog.text for value in SENSITIVE_VALUES)
    assert request_id_context.get() is None
