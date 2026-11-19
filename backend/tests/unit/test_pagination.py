from typing import Annotated

import pytest
from fastapi import Depends

from app.core.pagination import MAX_PAGE_LIMIT, Page, Pagination, pagination


@pytest.fixture
def paginated_client(application, client):
    @application.get("/test-page")
    def page(params: Annotated[Pagination, Depends(pagination)]):
        return Page[int](items=[], total=0, limit=params.limit, offset=params.offset)

    return client


def test_default_page(paginated_client):
    response = paginated_client.get("/test-page")
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": 20, "offset": 0}


def test_max_limit(paginated_client):
    response = paginated_client.get("/test-page", params={"limit": MAX_PAGE_LIMIT})
    assert response.status_code == 200
    assert response.json()["limit"] == MAX_PAGE_LIMIT


@pytest.mark.parametrize("query", [{"limit": 101}, {"limit": 0}, {"offset": -1}])
def test_invalid_page(paginated_client, query):
    response = paginated_client.get("/test-page", params=query)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_page_schema():
    assert Page[str](items=["item"], total=1, limit=20, offset=0).model_dump() == {
        "items": ["item"],
        "total": 1,
        "limit": 20,
        "offset": 0,
    }
