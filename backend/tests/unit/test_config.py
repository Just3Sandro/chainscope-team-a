import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app


@pytest.mark.parametrize("origins", ["*", "https://*.example.test"])
def test_cors_wildcard_is_refused(monkeypatch, origins):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", origins)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_database_url_is_required(monkeypatch):
    monkeypatch.delenv("DATABASE_URL")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_prod_disables_docs():
    application = create_app(Settings(_env_file=None, app_env="prod"))
    assert application.debug is False
    with TestClient(application) as client:
        for path in ("/docs", "/redoc", "/openapi.json"):
            assert client.get(path).status_code == 404


def test_cors_is_disabled_by_default(client):
    response = client.get(
        "/api/v1/health", headers={"Origin": "https://ui.example.test"}
    )
    assert "access-control-allow-origin" not in response.headers


def test_explicit_cors_origin():
    origin = "https://ui.example.test"
    application = create_app(Settings(_env_file=None, cors_allowed_origins=origin))
    with TestClient(application) as client:
        allowed = client.get("/api/v1/health", headers={"Origin": origin})
        denied = client.get(
            "/api/v1/health", headers={"Origin": "https://other.example.test"}
        )
    assert allowed.headers["access-control-allow-origin"] == origin
    assert "access-control-allow-origin" not in denied.headers


def test_rejected_cors_preflight_is_normalized():
    application = create_app(
        Settings(_env_file=None, cors_allowed_origins="https://ui.example.test")
    )
    with TestClient(application) as client:
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "https://other.example.test",
                "Access-Control-Request-Method": "GET",
            },
        )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]
