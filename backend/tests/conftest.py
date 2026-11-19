import os

import pytest
from fastapi.testclient import TestClient

# URL fictive : aucune connexion n’est ouverte pendant ces tests.
TEST_DATABASE_URL = "postgresql+psycopg://test:change-me@postgres:5432/test"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["APP_ENV"] = "test"
os.environ["CORS_ALLOWED_ORIGINS"] = ""

from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture
def application():
    return create_app(Settings(_env_file=None))


@pytest.fixture
def client(application):
    with TestClient(application, raise_server_exceptions=False) as test_client:
        yield test_client
